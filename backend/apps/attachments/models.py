import uuid

from django.conf import settings
from django.db import models


class Attachment(models.Model):
    access_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    file = models.FileField(upload_to="attachments/%Y/%m/")
    filename = models.CharField(max_length=255)
    size = models.PositiveIntegerField()
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="attachments"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "attachments"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.filename
