from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class InboxMessage(models.Model):
    KIND_SYSTEM = "system"
    KIND_USER = "user"
    KIND_CHOICES = (
        (KIND_SYSTEM, "System"),
        (KIND_USER, "User"),
    )

    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sent_inbox_messages",
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="replies",
    )
    recipients = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="InboxMessageRecipient",
        related_name="inbox_messages",
    )
    attachments = models.ManyToManyField(
        "attachments.Attachment",
        blank=True,
        related_name="inbox_messages",
    )
    content_type = models.ForeignKey(
        ContentType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    object_id = models.CharField(max_length=255, blank=True, default="", db_index=True)
    content_object = GenericForeignKey("content_type", "object_id")
    resource_key = models.CharField(max_length=50, blank=True, default="")
    resource_label = models.CharField(max_length=255, blank=True, default="")
    body = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "inbox_messages"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at", "-id"], name="inbox_message_time_idx"),
        ]

    def __str__(self):
        sender = self.sender or "system"
        return f"{self.kind} message from {sender}"


class InboxMessageRecipient(models.Model):
    message = models.ForeignKey(
        InboxMessage,
        on_delete=models.CASCADE,
        related_name="recipient_states",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="inbox_recipient_states",
    )
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "inbox_message_recipients"
        unique_together = ("message", "user")
        indexes = [
            models.Index(fields=["user", "read_at"]),
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["user", "read_at", "message"], name="inbox_rec_user_read_msg_idx"),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} -> {self.message_id}"
