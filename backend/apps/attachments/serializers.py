from django.urls import reverse
from rest_framework import serializers

from .models import Attachment


class AttachmentFileField(serializers.FileField):
    def get_attribute(self, instance):
        return instance

    def to_representation(self, attachment):
        if not attachment.file:
            return None

        url = reverse(
            "attachment-download",
            kwargs={"access_key": attachment.access_key},
        )
        return url


class AttachmentSerializer(serializers.ModelSerializer):
    file = AttachmentFileField()
    uploaded_by_name = serializers.CharField(source="uploaded_by.username", read_only=True)

    class Meta:
        model = Attachment
        fields = (
            "id",
            "access_key",
            "file",
            "filename",
            "size",
            "uploaded_by",
            "uploaded_by_name",
            "uploaded_at",
        )
        read_only_fields = (
            "id",
            "access_key",
            "filename",
            "size",
            "uploaded_by",
            "uploaded_at",
        )
