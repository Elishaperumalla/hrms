import uuid
from datetime import timedelta

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

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

        if not was_online:
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

        receipt_data = await self.mark_unread_as_read(
            self.conversation_id,
            user.pk,
        )

        if receipt_data:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "receipt_update",
                    "action": "read",
                    "user_id": user.pk,
                    "message_ids": receipt_data,
                },
            )

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

            was_online = ChatPresenceConnection.objects.filter(
                user_id=user_id,
                last_seen__gte=cutoff,
            ).exists()

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

            still_online = ChatPresenceConnection.objects.filter(
                user_id=user_id,
                last_seen__gte=cutoff,
            ).exists()

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
