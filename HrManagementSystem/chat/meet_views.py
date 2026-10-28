import logging
import os
import secrets

from cryptography.fernet import Fernet
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_GET
from google_auth_oauthlib.flow import Flow

from .models import (
    GoogleMeetCredential,
    ScheduledMeeting,
    ConversationMember,
    Message,
    MessageReceipt,
)


logger = logging.getLogger(__name__)


GOOGLE_MEET_SCOPES = [
    "https://www.googleapis.com/auth/meetings.space.created",
    "https://www.googleapis.com/auth/calendar.events",
]


def _google_client_config():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError("Google OAuth credentials are not configured.")

    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [
                os.getenv(
                    "GOOGLE_REDIRECT_URI",
                    "https://voiceorbit.in/chat/meet/oauth/callback/",
                )
            ],
        }
    }


def _encrypt_token(value):
    key = os.getenv("GOOGLE_TOKEN_ENCRYPTION_KEY")

    if not key:
        raise RuntimeError("Google token encryption key is not configured.")

    return Fernet(key.encode()).encrypt(value.encode()).decode()


@login_required
@require_GET
def google_meet_connect(request):
    try:
        code_verifier = secrets.token_urlsafe(64)

        flow = Flow.from_client_config(
            _google_client_config(),
            scopes=GOOGLE_MEET_SCOPES,
            code_verifier=code_verifier,
        )
        flow.redirect_uri = os.getenv(
            "GOOGLE_REDIRECT_URI",
            "https://voiceorbit.in/chat/meet/oauth/callback/",
        )

        authorization_url, state = flow.authorization_url(
            access_type="offline",
            prompt="consent",
            include_granted_scopes="true",
        )

        request.session["google_meet_oauth_state"] = state
        request.session["google_meet_code_verifier"] = code_verifier

        return redirect(authorization_url)

    except Exception:
        messages.error(
            request,
            "Could not start Google Meet connection. "
            "Please verify the Google OAuth configuration.",
        )
        return redirect("chat:home")


@login_required
@require_GET
def google_meet_callback(request):
    if request.GET.get("error"):
        messages.error(
            request,
            "Google account connection was cancelled or denied.",
        )
        return redirect("chat:home")

    expected_state = request.session.pop(
        "google_meet_oauth_state",
        None,
    )
    code_verifier = request.session.pop(
        "google_meet_code_verifier",
        None,
    )
    received_state = request.GET.get("state")

    if (
        not expected_state
        or not received_state
        or expected_state != received_state
        or not code_verifier
    ):
        messages.error(
            request,
            "Google OAuth state validation failed. Please try connecting again.",
        )
        return redirect("chat:home")

    code = request.GET.get("code")
    if not code:
        messages.error(
            request,
            "Google did not return an authorization code.",
        )
        return redirect("chat:home")

    try:
        flow = Flow.from_client_config(
            _google_client_config(),
            scopes=GOOGLE_MEET_SCOPES,
            state=expected_state,
            code_verifier=code_verifier,
        )
        flow.redirect_uri = os.getenv(
            "GOOGLE_REDIRECT_URI",
            "https://voiceorbit.in/chat/meet/oauth/callback/",
        )
        flow.fetch_token(code=code)

        credentials = flow.credentials

        if not credentials.token:
            raise RuntimeError("Google did not return an access token.")

        credential, _ = GoogleMeetCredential.objects.get_or_create(
            user=request.user,
            defaults={
                "encrypted_access_token": "",
                "encrypted_refresh_token": "",
            },
        )

        credential.encrypted_access_token = _encrypt_token(
            credentials.token
        )

        # Google may omit a refresh token when an account has already
        # granted consent. Preserve the previously stored one in that case.
        if credentials.refresh_token:
            credential.encrypted_refresh_token = _encrypt_token(
                credentials.refresh_token
            )

        credential.token_expiry = credentials.expiry
        credential.save(
            update_fields=[
                "encrypted_access_token",
                "encrypted_refresh_token",
                "token_expiry",
                "updated_at",
            ]
        )

        messages.success(
            request,
            "Google account connected successfully for Meet creation.",
        )

    except Exception:
        logger.exception(
            "Google Meet OAuth callback failed for user_id=%s",
            request.user.pk,
        )
        messages.error(
            request,
            "Google account connection failed. Please check OAuth settings "
            "and try again.",
        )

    return redirect("chat:home")


# --------------------------------------------------
# Google Meet API — token refresh and meeting creation
# --------------------------------------------------

import json
from datetime import datetime, timedelta, timezone as dt_timezone
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials


def _decrypt_token(value):
    key = os.getenv("GOOGLE_TOKEN_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError("Google token encryption key is not configured.")
    if not value:
        return ""
    return Fernet(key.encode()).decrypt(value.encode()).decode()


def _get_valid_google_credentials(credential):
    """Decrypt and refresh the user's stored Google OAuth credentials."""
    access_token = _decrypt_token(credential.encrypted_access_token)
    refresh_token = _decrypt_token(credential.encrypted_refresh_token)

    expiry = credential.token_expiry
    if expiry is not None and expiry.tzinfo is not None:
        expiry = expiry.astimezone(dt_timezone.utc).replace(tzinfo=None)

    credentials = Credentials(
        token=access_token or None,
        refresh_token=refresh_token or None,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        scopes=GOOGLE_MEET_SCOPES,
        expiry=expiry,
    )

    # google-auth compares expiry against a naive UTC datetime.
    # Normalize expiry on the Credentials object before checking validity.
    if credentials.expiry is not None and credentials.expiry.tzinfo is not None:
        credentials.expiry = credentials.expiry.astimezone(
            dt_timezone.utc
        ).replace(tzinfo=None)

    if not credentials.valid:
        if not credentials.refresh_token:
            raise RuntimeError(
                "Google connection expired. Reconnect your Google account."
            )

        credentials.refresh(GoogleAuthRequest())

        credential.encrypted_access_token = _encrypt_token(
            credentials.token
        )
        if credentials.refresh_token:
            credential.encrypted_refresh_token = _encrypt_token(
                credentials.refresh_token
            )
        credential.token_expiry = credentials.expiry
        credential.save(update_fields=[
            "encrypted_access_token",
            "encrypted_refresh_token",
            "token_expiry",
            "updated_at",
        ])

    return credentials


@login_required
@require_POST
def google_meet_create(request):
    """Create a real Google Meet space for the connected account."""
    credential = GoogleMeetCredential.objects.filter(
        user=request.user
    ).first()

    if not credential:
        return JsonResponse({
            "ok": False,
            "error": "Connect your Google account before creating a meeting.",
            "connect_url": reverse("chat:meet_connect"),
        }, status=400)

    try:
        credentials = _get_valid_google_credentials(credential)

        response = requests.post(
            "https://meet.googleapis.com/v2/spaces",
            headers={
                "Authorization": f"Bearer {credentials.token}",
                "Content-Type": "application/json",
            },
            json={},
            timeout=20,
        )

        if not response.ok:
            logger.error(
                "Google Meet API failed for user_id=%s status=%s body=%s",
                request.user.pk,
                response.status_code,
                response.text[:1000],
            )
            return JsonResponse({
                "ok": False,
                "error": (
                    "Google Meet could not create the meeting. "
                    "Please reconnect your Google account and try again."
                ),
            }, status=502)

        data = response.json()
        meeting_uri = data.get("meetingUri", "")
        parsed_uri = urlparse(meeting_uri)

        if (
            parsed_uri.scheme != "https"
            or parsed_uri.netloc.lower() != "meet.google.com"
            or not parsed_uri.path.strip("/")
        ):
            logger.error(
                "Google Meet returned an invalid meeting URI for user_id=%s",
                request.user.pk,
            )
            return JsonResponse({
                "ok": False,
                "error": "Google returned an invalid meeting link.",
            }, status=502)

        return JsonResponse({
            "ok": True,
            "meeting_url": meeting_uri,
            "meeting_name": data.get("name", ""),
        })

    except Exception:
        logger.exception(
            "Google Meet creation failed for user_id=%s",
            request.user.pk,
        )
        return JsonResponse({
            "ok": False,
            "error": (
                "Meeting creation failed. Please check your Google "
                "connection and try again."
            ),
        }, status=500)


# --------------------------------------------------
# Scheduled Google Meet — Google Calendar API
# --------------------------------------------------

from zoneinfo import ZoneInfo
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


@login_required
@require_POST
def google_meet_schedule(request):
    """Create a Calendar event with a Google Meet link and share it in chat."""
    try:
        payload = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {"ok": False, "error": "Invalid request data."},
            status=400,
        )

    if not isinstance(payload, dict):
        return JsonResponse(
            {"ok": False, "error": "Invalid request data."},
            status=400,
        )

    title = str(payload.get("title", "")).strip()
    description = str(payload.get("description", "")).strip()
    conversation_id = payload.get("conversation_id")
    start_value = payload.get("start_time")
    end_value = payload.get("end_time")

    if not title or len(title) > 200:
        return JsonResponse(
            {"ok": False, "error": "Enter a title (maximum 200 characters)."},
            status=400,
        )

    try:
        conversation_id = int(conversation_id)
        if conversation_id <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return JsonResponse(
            {"ok": False, "error": "Select a valid conversation."},
            status=400,
        )

    membership = ConversationMember.objects.filter(
        conversation_id=conversation_id,
        user=request.user,
    ).select_related("conversation").first()

    if membership is None:
        return JsonResponse(
            {"ok": False, "error": "You are not a member of that conversation."},
            status=403,
        )

    try:
        zone = ZoneInfo("Asia/Kolkata")
        start_time = datetime.fromisoformat(str(start_value))
        end_time = datetime.fromisoformat(str(end_value))

        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=zone)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=zone)

        if end_time <= start_time:
            raise ValueError("End time must be after start time.")

        if start_time <= timezone.now():
            raise ValueError("Choose a future start time.")

        if end_time - start_time > timedelta(hours=24):
            raise ValueError("Meeting duration cannot exceed 24 hours.")

    except (TypeError, ValueError, OverflowError):
        return JsonResponse(
            {
                "ok": False,
                "error": (
                    "Enter valid future start and end times. "
                    "The end time must be after the start time."
                ),
            },
            status=400,
        )

    credential = GoogleMeetCredential.objects.filter(
        user=request.user
    ).first()

    if credential is None:
        return JsonResponse(
            {
                "ok": False,
                "error": "Connect your Google account before scheduling a meeting.",
                "connect_url": reverse("chat:meet_connect"),
            },
            status=403,
        )

    # Only invite users who belong to this conversation and have an email.
    attendee_emails = list(
        ConversationMember.objects.filter(
            conversation_id=conversation_id,
        ).exclude(
            user__email="",
        ).exclude(
            user__email__isnull=True,
        ).values_list("user__email", flat=True).distinct()
    )

    try:
        credentials = _get_valid_google_credentials(credential)

        event_payload = {
            "summary": title,
            "description": description,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "Asia/Kolkata",
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "Asia/Kolkata",
            },
            "attendees": [{"email": email} for email in attendee_emails],
            "conferenceData": {
                "createRequest": {
                    "requestId": secrets.token_urlsafe(24),
                    "conferenceSolutionKey": {"type": "hangoutsMeet"},
                }
            },
        }

        response = requests.post(
            "https://www.googleapis.com/calendar/v3/calendars/primary/events",
            params={
                "conferenceDataVersion": 1,
                "sendUpdates": "all",
            },
            headers={
                "Authorization": f"Bearer {credentials.token}",
                "Content-Type": "application/json",
            },
            json=event_payload,
            timeout=30,
        )

        try:
            event_data = response.json()
        except ValueError:
            event_data = {}

        if not response.ok:
            logger.error(
                "Google Calendar event creation failed for user_id=%s status=%s",
                request.user.pk,
                response.status_code,
            )
            if response.status_code in (401, 403):
                return JsonResponse(
                    {
                        "ok": False,
                        "error": (
                            "Google Calendar permission is missing. "
                            "Reconnect your Google account and grant Calendar access."
                        ),
                        "connect_url": reverse("chat:meet_connect"),
                    },
                    status=403,
                )

            return JsonResponse(
                {
                    "ok": False,
                    "error": (
                        "Google Calendar could not create the event. "
                        "Please try again."
                    ),
                },
                status=502,
            )

        event_id = event_data.get("id", "")
        meeting_url = (
            event_data.get("hangoutLink")
            or next(
                (
                    item.get("uri", "")
                    for item in event_data.get(
                        "conferenceData", {}
                    ).get("entryPoints", [])
                    if item.get("entryPointType") == "video"
                ),
                "",
            )
        )

        parsed_url = urlparse(meeting_url)
        if (
            not event_id
            or parsed_url.scheme != "https"
            or parsed_url.netloc.lower() != "meet.google.com"
            or not parsed_url.path.strip("/")
        ):
            logger.error(
                "Calendar event response lacked a valid Meet URL for user_id=%s",
                request.user.pk,
            )
            return JsonResponse(
                {
                    "ok": False,
                    "error": (
                        "The calendar event was created, but Google did not "
                        "return a usable Meet link. Check your Google Calendar."
                    ),
                },
                status=502,
            )

        scheduled = ScheduledMeeting.objects.create(
            conversation=membership.conversation,
            organizer=request.user,
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            timezone_name="Asia/Kolkata",
            meeting_url=meeting_url,
            google_event_id=event_id,
            attendee_emails=attendee_emails,
        )

        local_start = timezone.localtime(
            scheduled.start_time, ZoneInfo("Asia/Kolkata")
        ).strftime("%d %b %Y, %I:%M %p")
        local_end = timezone.localtime(
            scheduled.end_time, ZoneInfo("Asia/Kolkata")
        ).strftime("%I:%M %p")

        chat_text = (
            f"📅 Scheduled meeting: {title}\n"
            f"Date: {local_start} – {local_end} IST\n"
            f"Join Google Meet: {meeting_url}"
        )

        message = Message.objects.create(
            conversation=membership.conversation,
            sender=request.user,
            content=chat_text,
        )

        recipient_ids = list(
            ConversationMember.objects.filter(
                conversation_id=conversation_id,
            ).exclude(
                user_id=request.user.pk,
            ).values_list("user_id", flat=True)
        )

        MessageReceipt.objects.bulk_create([
            MessageReceipt(message=message, user_id=user_id)
            for user_id in recipient_ids
        ])

        conversation = membership.conversation
        conversation.updated_at = timezone.now()
        conversation.save(update_fields=["updated_at"])

        # Broadcast using the same event shape as ordinary chat messages.
        try:
            channel_layer = get_channel_layer()
            if channel_layer is not None:
                async_to_sync(channel_layer.group_send)(
                    f"chat_{conversation_id}",
                    {
                        "type": "chat_message",
                        "id": message.pk,
                        "message": message.content,
                        "sender_id": request.user.pk,
                        "sender_name": (
                            request.user.get_full_name()
                            or request.user.username
                        ),
                        "created_at": timezone.localtime(
                            message.created_at
                        ).strftime("%I:%M %p"),
                        "reply_to": None,
                        "forwarded_from": None,
                    },
                )
        except Exception:
            logger.exception(
                "Scheduled meeting was saved but chat broadcast failed "
                "for conversation_id=%s",
                conversation_id,
            )

        return JsonResponse({
            "ok": True,
            "meeting_id": scheduled.pk,
            "meeting_url": meeting_url,
            "event_id": event_id,
            "message": "Meeting scheduled and shared in the conversation.",
        })

    except Exception:
        logger.exception(
            "Scheduled Google Meet creation failed for user_id=%s",
            request.user.pk,
        )
        return JsonResponse(
            {
                "ok": False,
                "error": (
                    "Could not schedule the meeting. "
                    "Check the server logs for details."
                ),
            },
            status=502,
        )
