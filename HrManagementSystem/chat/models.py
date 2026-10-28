
from django.conf import settings
from django.db import models
from django.utils import timezone


class Conversation(models.Model):
    class ChatType(models.TextChoices):
        INDIVIDUAL = "INDIVIDUAL", "Individual"
        TEAM = "TEAM", "Team"
        DEPARTMENT = "DEPARTMENT", "Department"
        BRANCH = "BRANCH", "Branch"
        COMPANY = "COMPANY", "Company"

    chat_type = models.CharField(
        max_length=20,
        choices=ChatType.choices,
    )
    name = models.CharField(max_length=150, blank=True)
    company = models.ForeignKey(
        "organization.Company",
        on_delete=models.CASCADE,
        related_name="chat_conversations",
        null=True,
        blank=True,
    )
    department = models.ForeignKey(
        "organization.Department",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="chat_conversations",
    )
    branch = models.ForeignKey(
        "organization.Branch",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="chat_conversations",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_chat_conversations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-updated_at"]  # noqa: RUF012

    def __str__(self):
        return self.name or f"{self.get_chat_type_display()} #{self.pk}"


class ConversationMember(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_memberships",
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=["conversation", "user"],
                name="unique_chat_conversation_member",
            ),
        ]

    def __str__(self):
        return f"{self.user} - {self.conversation}"


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_chat_messages",
    )
    content = models.TextField(max_length=5000)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)
   
    reply_to = models.ForeignKey(
    "self",
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="replies",)

    forwarded_from = models.ForeignKey(
    "self",
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="forwards",)

    class Meta:
        ordering = ["created_at"]  # noqa: RUF012

    def __str__(self):
        return f"{self.sender} - {self.created_at:%Y-%m-%d %H:%M}"

class MessageReceipt(models.Model):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="receipts",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_message_receipts",
    )
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [  # noqa: RUF012
            models.UniqueConstraint(
                fields=["message", "user"],
                name="unique_chat_message_receipt",
            ),
        ]
        ordering = ["user_id"]  # noqa: RUF012

    def __str__(self):
        return f"Message {self.message_id} → {self.user_id}"


    

class ChatPresenceConnection(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_presence_connections",
    )
    connection_id = models.CharField(
        max_length=64,
        unique=True,
    )
    last_seen = models.DateTimeField(
        default=timezone.now,
        db_index=True,
    )

    class Meta:
        indexes = [  # noqa: RUF012
            models.Index(fields=["user", "last_seen"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.connection_id}"

class GoogleMeetCredential(models.Model):
    """
    Stores encrypted Google OAuth tokens for each HRMS user.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="google_meet_credential",
    )
    encrypted_access_token = models.TextField()
    encrypted_refresh_token = models.TextField(blank=True, default="")
    token_expiry = models.DateTimeField(null=True, blank=True)
    google_email = models.EmailField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Google Meet credential for user {self.user_id}"


class ScheduledMeeting(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        CANCELLED = "CANCELLED", "Cancelled"

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="scheduled_meetings",
    )
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organized_scheduled_meetings",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    timezone_name = models.CharField(
        max_length=64,
        default="Asia/Kolkata",
    )
    meeting_url = models.URLField(max_length=500, blank=True)
    google_event_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )
    attendee_emails = models.JSONField(default=list, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start_time"]

    def __str__(self):
        return f"{self.title} ({self.start_time:%Y-%m-%d %H:%M})"
