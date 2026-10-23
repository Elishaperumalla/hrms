from datetime import timedelta

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

from attendance.models import Attendance
from .models import ChatPresenceConnection, ConversationMember


PRESENCE_TIMEOUT_SECONDS = 75


def user_is_checked_in(user_id):
    """True only when today's attendance is checked in, not checked out."""
    return Attendance.objects.filter(
        employee__user_id=user_id,
        employee__employment_status="ACTIVE",
        employee__user__is_active=True,
        date=timezone.localdate(),
        check_in__isnull=False,
        check_out__isnull=True,
    ).exists()


def has_fresh_presence_connection(user_id):
    cutoff = timezone.now() - timedelta(
        seconds=PRESENCE_TIMEOUT_SECONDS
    )

    return ChatPresenceConnection.objects.filter(
        user_id=user_id,
        last_seen__gte=cutoff,
    ).exists()


def checked_in_user_ids(user_ids):
    if not user_ids:
        return set()

    return set(
        Attendance.objects.filter(
            employee__user_id__in=user_ids,
            employee__employment_status="ACTIVE",
            employee__user__is_active=True,
            date=timezone.localdate(),
            check_in__isnull=False,
            check_out__isnull=True,
        ).values_list("employee__user_id", flat=True).distinct()
    )


def broadcast_user_presence(user_id, online=None):
    """
    online=None: broadcast Online only when checked in and connected.
    online=False: force Offline, for example after clock-out.
    """
    if online is None:
        if not user_is_checked_in(user_id):
            return

        if not has_fresh_presence_connection(user_id):
            return

        online = True

    elif online and not (
        user_is_checked_in(user_id)
        and has_fresh_presence_connection(user_id)
    ):
        online = False

    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    conversation_ids = ConversationMember.objects.filter(
        user_id=user_id,
    ).values_list("conversation_id", flat=True).distinct()

    for conversation_id in conversation_ids:
        async_to_sync(channel_layer.group_send)(
            f"chat_{conversation_id}",
            {
                "type": "presence_update",
                "user_id": user_id,
                "online": online,
            },
        )
