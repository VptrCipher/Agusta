import secrets

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


def generate_api_key():
    return f"agusta_{secrets.token_urlsafe(32)}"


class User(AbstractUser):
    class AuthType(models.TextChoices):
        LOCAL = "local", "Local Password"
        LDAP = "ldap", "LDAP"

    avatar_attachment = models.ForeignKey(
        "attachments.Attachment",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="avatar_users",
    )
    mobile_phone = models.CharField(max_length=20, blank=True, default="")
    auth_type = models.CharField(max_length=20, choices=AuthType.choices, default=AuthType.LOCAL)
    notify_on_playbook_completion = models.BooleanField(default=True)
    notify_on_case_assignment = models.BooleanField(default=True)

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def role(self):
        if self.is_superuser:
            return "admin"
        groups = set(self.groups.values_list("name", flat=True))
        if "viewer" in groups:
            return "viewer"
        if "user" in groups:
            return "user"
        return "user"


class UserApiKey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="api_keys")
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=128, unique=True, default=generate_api_key)
    expires_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_api_keys"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.user})"

    @property
    def is_expired(self):
        return bool(self.expires_at and self.expires_at <= timezone.now())

    def refresh_key(self):
        self.key = generate_api_key()
        return self.key
