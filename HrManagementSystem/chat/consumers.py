import uuid
from datetime import timedelta

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .presence import checked_in_user_ids, user_is_checked_in

from .models import (
    ChatPresenceConnection,
    Conversation,
    ConversationMember,
    Message,
    MessageReceipt,
)

PRESENCE_TIMEOUT_SECONDS = 75


class ChatConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        user = self.scope["user"]

        if not user.is_authenticated:
            await self.close(code=4401)
            return

        try:
            self.conversation_id = int(
                self.scope["url_route"]["kwargs"]["conversation_id"]
            )
        except (ValueError, TypeError, KeyError):
            await self.close(code=4400)
            return

        if not await self.is_member(user.pk, self.conversation_id):
            await self.close(code=4403)
            return

        self.room_group_name = f"chat_{self.conversation_id}"
        self.presence_connection_id = uuid.uuid4().hex

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )
        await self.accept()

        was_online, conversation_ids = await self.register_presence(
            user.pk,
            self.presence_connection_id,
        )

        if (
            not was_online
            and await self.is_attendance_checked_in(user.pk)
        ):
            await self.broadcast_presence(
                conversation_ids, user.pk, True
            )

        snapshot = await self.get_presence_snapshot(
            self.conversation_id
        )

        await self.send_json({
            "type": "presence_snapshot",
            "members": snapshot,
        })

        can_write = await self.can_write_chat(user)
        await self.send_json({
            "type": "chat_permission",
            "can_write": can_write,
            "message": (
                "You’re currently checked out. "
                "Please check in to start chatting with your colleagues."
            ),
        })

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

        connection_id = getattr(
            self, "presence_connection_id", None
        )
        user = self.scope.get("user")

        if connection_id and user and user.is_authenticated:
            should_broadcast_offline, conversation_ids = (
                await self.remove_presence(
                    user.pk, connection_id
                )
            )

            if should_broadcast_offline:
                await self.broadcast_presence(
                    conversation_ids, user.pk, False
                )

    async def receive_json(self, content, **kwargs):
        user = self.scope["user"]

        if not user.is_authenticated:
            await self.close(code=4401)
            return

        if not isinstance(content, dict):
            return

        if not await self.is_member(
            user.pk, self.conversation_id
        ):
            await self.close(code=4403)
            return

        action = content.get("action", "message")

        if action == "heartbeat":
            await self.update_presence_heartbeat(
                user.pk,
                self.presence_connection_id,
            )
            can_write = await self.can_write_chat(user)
            await self.send_json({
                "type": "chat_permission",
                "can_write": can_write,
                "message": (
                    "You’re currently checked out. "
                    "Please check in to start chatting with your colleagues."
                ),
            })
            return

        # Checked-out users can receive and read messages, but cannot
        # create, edit, delete, reply to, or forward messages.
        if action in {"message", "edit", "delete", "forward"}:
            if not await self.can_write_chat(user):
                await self.send_json({
                    "type": "chat_permission",
                    "can_write": False,
                    "message": (
                        "You’re currently checked out. "
                        "Please check in to start chatting with your colleagues."
                    ),
                })
                return

        # ------------------------------------------
        # NORMAL MESSAGE + OPTIONAL REPLY
        # ------------------------------------------
        if action == "message":
            text = content.get("message", "")

            if not isinstance(text, str):
                return

            text = text.strip()

            if not text or len(text) > 5000:
                return

            reply_to_id = content.get("reply_to_id")

            if reply_to_id in ("", None):
                reply_to_id = None
            elif not self.valid_id(reply_to_id):
                return
            else:
                reply_to_id = int(reply_to_id)

            saved = await self.save_message(
                conversation_id=self.conversation_id,
                user_id=user.pk,
                content=text,
                reply_to_id=reply_to_id,
            )

            if saved is None:
                return

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    **saved,
                },
            )
            await self.broadcast_sidebar_updates(
                self.conversation_id,
                user.pk,
                text,
            )
        # ------------------------------------------
        # EDIT OWN MESSAGE
        # ------------------------------------------
        elif action == "edit":
            message_id = content.get("message_id")
            new_text = content.get("message", "")

            if not self.valid_id(message_id):
                return

            if not isinstance(new_text, str):
                return

            new_text = new_text.strip()

            if not new_text or len(new_text) > 5000:
                await self.send_json({
                    "type": "message_action_result",
                    "action": "edit",
                    "success": False,
                    "message": "Message cannot be empty or exceed 5000 characters.",
                })
                return

            updated = await self.edit_message(
                conversation_id=self.conversation_id,
                message_id=int(message_id),
                user_id=user.pk,
                new_text=new_text,
            )

            if not updated:
                await self.send_json({
                    "type": "message_action_result",
                    "action": "edit",
                    "success": False,
                    "message": "You can edit only your own messages.",
                })
                return

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message_edited",
                    **updated,
                },
            )

        # ------------------------------------------
        # DELETE OWN MESSAGE
        # ------------------------------------------
        elif action == "delete":
            message_id = content.get("message_id")

            if not self.valid_id(message_id):
                return

            deleted = await self.delete_message(
                conversation_id=self.conversation_id,
                message_id=int(message_id),
                user_id=user.pk,
            )

            if not deleted:
                await self.send_json({
                    "type": "message_action_result",
                    "action": "delete",
                    "success": False,
                    "message": "You can delete only your own messages.",
                })
                return

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message_deleted",
                    "message_id": int(message_id),
                },
            )
        # ------------------------------------------
        # FORWARD MESSAGE TO ANOTHER CONVERSATION
        # ------------------------------------------
        elif action == "forward":
            message_id = content.get("message_id")
            target_id = content.get("target_conversation_id")

            if not self.valid_id(message_id):
                return

            if not self.valid_id(target_id):
                return

            forwarded = await self.forward_message(
                source_conversation_id=self.conversation_id,
                message_id=int(message_id),
                target_conversation_id=int(target_id),
                user_id=user.pk,
            )

            if not forwarded:
                await self.send_json({
                    "type": "forward_result",
                    "success": False,
                    "message": (
                        "Unable to forward this message "
                        "to the selected chat."
                    ),
                })
                return

            destination_id, saved = forwarded

            await self.channel_layer.group_send(
                f"chat_{destination_id}",
                {
                    "type": "chat_message",
                    **saved,
                },
            )

            await self.send_json({
                "type": "forward_result",
                "success": True,
                "message": "Message forwarded successfully.",
                "message_id": message_id,
                "target_conversation_id": destination_id,
            })

        # ------------------------------------------
        # DELIVERED RECEIPTS
        # ------------------------------------------
        elif action == "delivered":
            message_id = content.get("message_id")

            if not self.valid_id(message_id):
                return

            updated = await self.mark_delivered(
                int(message_id),
                user.pk,
                self.conversation_id,
            )

            if updated:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "receipt_update",
                        "action": "delivered",
                        "user_id": user.pk,
                        "message_ids": [updated],
                    },
                )

        # ------------------------------------------
        # READ RECEIPTS
        # ------------------------------------------
        elif action == "read":
            message_ids = content.get("message_ids", [])

            if not isinstance(message_ids, list):
                return

            updated_ids = await self.mark_read(
                message_ids,
                user.pk,
                self.conversation_id,
            )

            if updated_ids:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "receipt_update",
                        "action": "read",
                        "user_id": user.pk,
                        "message_ids": updated_ids,
                    },
                )

    @staticmethod
    def valid_id(value):
        if isinstance(value, bool):
            return False

        if isinstance(value, int):
            return value > 0

        return (
            isinstance(value, str)
            and value.isdigit()
            and int(value) > 0
        )

    async def chat_message(self, event):
        await self.send_json({
            "type": "message",
            "id": event["id"],
            "message": event["message"],
            "sender_id": event["sender_id"],
            "sender_name": event["sender_name"],
            "created_at": event["created_at"],
            "reply_to": event.get("reply_to"),
            "forwarded_from": event.get("forwarded_from"),
        })

    async def chat_message_edited(self, event):
        await self.send_json({
            "type": "message_edited",
            "id": event["id"],
            "message": event["message"],
            "edited_at": event["edited_at"],
        })

    async def chat_message_deleted(self, event):
        await self.send_json({
            "type": "message_deleted",
            "id": event["message_id"],
        })

    async def receipt_update(self, event):
        await self.send_json({
            "type": "receipt",
            "action": event["action"],
            "user_id": event["user_id"],
            "message_ids": event["message_ids"],
        })

    async def presence_update(self, event):
        await self.send_json({
            "type": "presence_update",
            "user_id": event["user_id"],
            "online": event["online"],
        })

    async def broadcast_presence(
        self, conversation_ids, user_id, online
    ):
        for conversation_id in conversation_ids:
            await self.channel_layer.group_send(
                f"chat_{conversation_id}",
                {
                    "type": "presence_update",
                    "user_id": user_id,
                    "online": online,
                },
            )

    async def broadcast_sidebar_updates(
        self, conversation_id, sender_id, message_text
    ):
        updates = await self.get_sidebar_update_data(
            conversation_id, sender_id, message_text
        )
        for update in updates:
            await self.channel_layer.group_send(
                f"chat_sidebar_{update['user_id']}",
                {
                    "type": "sidebar_update",
                    "conversationId": conversation_id,
                    "senderName": update["sender_name"],
                    "message": message_text,
                    "unreadCount": update["unread_count"],
                    "href": update["href"],
                    "chatTitle": update["chat_title"],
                    "chatType": update["chat_type"],
                },
            )

    @database_sync_to_async
    def get_sidebar_update_data(
        self, conversation_id, sender_id, message_text
    ):
        from django.urls import reverse

        conversation = Conversation.objects.filter(
            pk=conversation_id
        ).first()
        if conversation is None:
            return []

        members = list(
            ConversationMember.objects.filter(
                conversation_id=conversation_id
            ).select_related("user")
        )
        result = []
        for membership in members:
            user = membership.user
            unread_count = MessageReceipt.objects.filter(
                user_id=user.pk,
                message__conversation_id=conversation_id,
                read_at__isnull=True,
            ).exclude(message__sender_id=user.pk).count()

            if conversation.chat_type == Conversation.ChatType.INDIVIDUAL:
                other = next(
                    (m.user for m in members if m.user_id != user.pk),
                    None,
                )
                title = (
                    (other.get_full_name().strip() or other.username)
                    if other else "Individual Chat"
                )
            else:
                title = (
                    conversation.name
                    or (
                        f"{conversation.department.name} Department"
                        if conversation.department_id else None
                    )
                    or (
                        f"{conversation.branch.name} Branch"
                        if conversation.branch_id else None
                    )
                    or f"{conversation.get_chat_type_display()} Chat"
                )

            result.append({
                "user_id": user.pk,
                "sender_name": (
                    "You" if user.pk == sender_id
                    else (
                        self_name
                        if (self_name := (
                            get_user_model().objects.filter(pk=sender_id)
                            .values_list("first_name", flat=True).first()
                        )) else "Message"
                    )
                ),
                "unread_count": unread_count,
                "href": reverse("chat:room", args=[conversation_id]),
                "chat_title": title,
                "chat_type": conversation.chat_type,
            })
        return result

    @database_sync_to_async
    def is_member(self, user_id, conversation_id):
        return ConversationMember.objects.filter(
            user_id=user_id,
            conversation_id=conversation_id,
        ).filter(
            Q(conversation__company__is_active=True)
            | Q(conversation__company__isnull=True)
        ).exists()

    @database_sync_to_async
    def is_attendance_checked_in(self, user_id):
        return user_is_checked_in(user_id)

    async def can_write_chat(self, user):
        # HR Admin and Super Admin are exempt from attendance restrictions.
        if getattr(user, "role", "") in {"HR_ADMIN", "SUPER_ADMIN"}:
            return True

        return await self.is_attendance_checked_in(user.pk)

    @database_sync_to_async
    def register_presence(self, user_id, connection_id):
        now = timezone.now()
        cutoff = now - timedelta(
            seconds=PRESENCE_TIMEOUT_SECONDS
        )

        with transaction.atomic():
            ChatPresenceConnection.objects.filter(
                user_id=user_id,
                last_seen__lt=cutoff,
            ).delete()

            was_online = (
                user_is_checked_in(user_id)
                and ChatPresenceConnection.objects.filter(
                    user_id=user_id,
                    last_seen__gte=cutoff,
                ).exists()
            )

            ChatPresenceConnection.objects.create(
                user_id=user_id,
                connection_id=connection_id,
                last_seen=now,
            )

            conversation_ids = list(
                ConversationMember.objects.filter(
                    user_id=user_id,
                ).values_list("conversation_id", flat=True)
            )

        return was_online, conversation_ids

    @database_sync_to_async
    def remove_presence(self, user_id, connection_id):
        cutoff = timezone.now() - timedelta(
            seconds=PRESENCE_TIMEOUT_SECONDS
        )

        with transaction.atomic():
            ChatPresenceConnection.objects.filter(
                user_id=user_id,
                connection_id=connection_id,
            ).delete()

            ChatPresenceConnection.objects.filter(
                user_id=user_id,
                last_seen__lt=cutoff,
            ).delete()

            still_online = (
                user_is_checked_in(user_id)
                and ChatPresenceConnection.objects.filter(
                    user_id=user_id,
                    last_seen__gte=cutoff,
                ).exists()
            )

            conversation_ids = list(
                ConversationMember.objects.filter(
                    user_id=user_id,
                ).values_list("conversation_id", flat=True)
            )

        return not still_online, conversation_ids

    @database_sync_to_async
    def update_presence_heartbeat(self, user_id, connection_id):
        return ChatPresenceConnection.objects.filter(
            user_id=user_id,
            connection_id=connection_id,
        ).update(last_seen=timezone.now())

    @database_sync_to_async
    def get_presence_snapshot(self, conversation_id):
        cutoff = timezone.now() - timedelta(
            seconds=PRESENCE_TIMEOUT_SECONDS
        )

        member_ids = list(
            ConversationMember.objects.filter(
                conversation_id=conversation_id,
            ).values_list("user_id", flat=True)
        )

        online_ids = set(
            ChatPresenceConnection.objects.filter(
                user_id__in=member_ids,
                last_seen__gte=cutoff,
            ).values_list("user_id", flat=True).distinct()
        )

        online_ids &= checked_in_user_ids(member_ids)

        return [
            {
                "user_id": member_id,
                "online": member_id in online_ids,
            }
            for member_id in member_ids
        ]

    @database_sync_to_async
    def edit_message(
        self,
        conversation_id,
        message_id,
        user_id,
        new_text,
    ):
        with transaction.atomic():
            message = Message.objects.select_for_update().filter(
                pk=message_id,
                conversation_id=conversation_id,
                sender_id=user_id,
            ).first()

            if message is None:
                return None

            message.content = new_text
            message.edited_at = timezone.now()

            message.save(
                update_fields=["content", "edited_at"]
            )

            return {
                "id": message.pk,
                "message": message.content,
                "edited_at": timezone.localtime(
                    message.edited_at
                ).strftime("%I:%M %p"),
            }

    @database_sync_to_async
    def delete_message(
        self,
        conversation_id,
        message_id,
        user_id,
    ):
        with transaction.atomic():
            message = Message.objects.select_for_update().filter(
                pk=message_id,
                conversation_id=conversation_id,
                sender_id=user_id,
            ).first()

            if message is None:
                return False

            message.delete()
            return True

    @database_sync_to_async
    def save_message(
        self, conversation_id, user_id, content, reply_to_id=None
    ):
        with transaction.atomic():
            membership = ConversationMember.objects.filter(
                conversation_id=conversation_id,
                user_id=user_id,
            ).filter(
                Q(conversation__company__is_active=True)
                | Q(conversation__company__isnull=True)
            ).first()

            if not membership:
                return None

            conversation = Conversation.objects.get(
                pk=conversation_id
            )

            reply_to = None

            if reply_to_id is not None:
                reply_to = Message.objects.filter(
                    pk=reply_to_id,
                    conversation_id=conversation_id,
                ).select_related("sender").first()

                # A reply must reference a message in this chat.
                if reply_to is None:
                    return None

            User = get_user_model()
            sender = User.objects.get(pk=user_id)

            message = Message.objects.create(
                conversation=conversation,
                sender=sender,
                content=content,
                reply_to=reply_to,
            )

            recipient_ids = list(
                ConversationMember.objects.filter(
                    conversation_id=conversation_id,
                ).exclude(
                    user_id=user_id,
                ).values_list("user_id", flat=True)
            )

            MessageReceipt.objects.bulk_create([
                MessageReceipt(
                    message=message,
                    user_id=recipient_id,
                )
                for recipient_id in recipient_ids
            ])

            conversation.updated_at = timezone.now()
            conversation.save(update_fields=["updated_at"])

            return self.serialize_message(message, reply_to)

    @database_sync_to_async
    def forward_message(
        self,
        source_conversation_id,
        message_id,
        target_conversation_id,
        user_id,
    ):
        with transaction.atomic():
            # Sender must belong to the source chat.
            source_member = ConversationMember.objects.filter(
                conversation_id=source_conversation_id,
                user_id=user_id,
            ).filter(
                Q(conversation__company__is_active=True)
                | Q(conversation__company__isnull=True)
            ).select_related("conversation").first()

            if not source_member:
                return None

            original = Message.objects.filter(
                pk=message_id,
                conversation_id=source_conversation_id,
            ).select_related("sender", "conversation").first()

            if not original:
                return None

            target_member = ConversationMember.objects.filter(
                conversation_id=target_conversation_id,
                user_id=user_id,
            ).filter(
                Q(conversation__company__is_active=True)
                | Q(conversation__company__isnull=True)
            ).select_related("conversation").first()

            if not target_member:
                return None

            source_company_id = original.conversation.company_id
            target_company_id = target_member.conversation.company_id

            # Never forward across different companies.
            if source_company_id != target_company_id:
                return None

            target = target_member.conversation
            User = get_user_model()
            sender = User.objects.get(pk=user_id)

            forwarded = Message.objects.create(
                conversation=target,
                sender=sender,
                content=original.content,
                forwarded_from=original,
            )

            recipient_ids = list(
                ConversationMember.objects.filter(
                    conversation_id=target.pk,
                ).exclude(
                    user_id=user_id,
                ).values_list("user_id", flat=True)
            )

            MessageReceipt.objects.bulk_create([
                MessageReceipt(
                    message=forwarded,
                    user_id=recipient_id,
                )
                for recipient_id in recipient_ids
            ])

            target.updated_at = timezone.now()
            target.save(update_fields=["updated_at"])

            return target.pk, self.serialize_message(
                forwarded,
                forwarded_from=original,
            )

    @staticmethod
    def serialize_message(message, reply_to=None, forwarded_from=None):
        sender = message.sender

        reply_data = None
        if reply_to is not None:
            reply_data = {
                "id": reply_to.pk,
                "message": reply_to.content,
                "sender_id": reply_to.sender_id,
                "sender_name": (
                    reply_to.sender.get_full_name()
                    or reply_to.sender.username
                ),
            }

        forwarded_data = None
        if forwarded_from is not None:
            forwarded_data = {
                "id": forwarded_from.pk,
                "message": forwarded_from.content,
                "sender_id": forwarded_from.sender_id,
                "sender_name": (
                    forwarded_from.sender.get_full_name()
                    or forwarded_from.sender.username
                ),
            }

        return {
            "id": message.pk,
            "message": message.content,
            "sender_id": sender.pk,
            "sender_name": (
                sender.get_full_name() or sender.username
            ),
            "created_at": timezone.localtime(
                message.created_at
            ).strftime("%I:%M %p"),
            "reply_to": reply_data,
            "forwarded_from": forwarded_data,
        }

    @database_sync_to_async
    def mark_delivered(self, message_id, user_id, conversation_id):
        updated = MessageReceipt.objects.filter(
            message_id=message_id,
            message__conversation_id=conversation_id,
            user_id=user_id,
            delivered_at__isnull=True,
        ).update(delivered_at=timezone.now())

        return message_id if updated else None

    @database_sync_to_async
    def mark_read(self, message_ids, user_id, conversation_id):
        valid_ids = [
            int(value)
            for value in message_ids
            if self.valid_id(value)
        ]

        if not valid_ids:
            return []

        now = timezone.now()

        receipts = MessageReceipt.objects.filter(
            message_id__in=valid_ids,
            message__conversation_id=conversation_id,
            user_id=user_id,
            read_at__isnull=True,
        )

        updated_ids = list(
            receipts.values_list("message_id", flat=True)
        )

        receipts.update(delivered_at=now, read_at=now)

        ConversationMember.objects.filter(
            conversation_id=conversation_id,
            user_id=user_id,
        ).update(last_read_at=now)

        return updated_ids

    @database_sync_to_async
    def mark_unread_as_read(self, conversation_id, user_id):
        now = timezone.now()

        receipts = MessageReceipt.objects.filter(
            message__conversation_id=conversation_id,
            user_id=user_id,
            read_at__isnull=True,
        )

        ids = list(
            receipts.values_list("message_id", flat=True)
        )

        if ids:
            receipts.update(delivered_at=now, read_at=now)

        ConversationMember.objects.filter(
            conversation_id=conversation_id,
            user_id=user_id,
        ).update(last_read_at=now)

        return ids


class ChatSidebarConsumer(AsyncJsonWebsocketConsumer):
    """Per-user live updates for the chat sidebar."""

    async def connect(self):
        user = self.scope["user"]
        if not user.is_authenticated:
            await self.close(code=4401)
            return

        self.user_id = user.pk
        self.sidebar_group = f"chat_sidebar_{user.pk}"

        await self.channel_layer.group_add(
            self.sidebar_group, self.channel_name
        )
        await self.accept()

        await self.send_json({"type": "sidebar_connected"})

        # Send existing unread counts immediately after connecting.
        unread_counts = await self.get_initial_unread_counts(self.user_id)
        for item in unread_counts:
            await self.send_json({
                "type": "sidebar_update",
                "conversationId": item["conversation_id"],
                "unreadCount": item["unread_count"],
                "href": item["href"],
                "chatTitle": item["chat_title"],
                "chatType": item["chat_type"],
            })

    @database_sync_to_async
    def get_initial_unread_counts(self, user_id):
        from django.urls import reverse

        memberships = ConversationMember.objects.filter(
            user_id=user_id
        ).select_related(
            "conversation",
            "conversation__department",
            "conversation__branch",
        )

        result = []

        for membership in memberships:
            conversation = membership.conversation

            unread_count = MessageReceipt.objects.filter(
                user_id=user_id,
                message__conversation_id=conversation.pk,
                read_at__isnull=True,
            ).exclude(
                message__sender_id=user_id
            ).count()

            if conversation.chat_type == Conversation.ChatType.INDIVIDUAL:
                other_members = ConversationMember.objects.filter(
                    conversation_id=conversation.pk
                ).exclude(user_id=user_id).select_related("user")

                other = next(iter(other_members), None)
                title = (
                    (other.user.get_full_name().strip() or other.user.username)
                    if other else "Individual Chat"
                )
            else:
                title = (
                    conversation.name
                    or (
                        f"{conversation.department.name} Department"
                        if conversation.department_id else None
                    )
                    or (
                        f"{conversation.branch.name} Branch"
                        if conversation.branch_id else None
                    )
                    or f"{conversation.get_chat_type_display()} Chat"
                )

            result.append({
                "conversation_id": conversation.pk,
                "unread_count": unread_count,
                "href": reverse("chat:room", args=[conversation.pk]),
                "chat_title": title,
                "chat_type": conversation.chat_type,
            })

        return result

    async def disconnect(self, close_code):
        if hasattr(self, "sidebar_group"):
            await self.channel_layer.group_discard(
                self.sidebar_group, self.channel_name
            )

    async def sidebar_update(self, event):
        await self.send_json({
            "type": "sidebar_update",
            "conversationId": event.get("conversationId"),
            "senderName": event.get("senderName", "Message"),
            "message": event.get("message", ""),
            "unreadCount": event.get("unreadCount", 0),
            "href": event.get("href", ""),
            "chatTitle": event.get("chatTitle", ""),
            "chatType": event.get("chatType", "INDIVIDUAL"),
        })
