from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers


class ContentTypeField(serializers.PrimaryKeyRelatedField):
    def __init__(self, **kwargs):
        super().__init__(queryset=ContentType.objects.all(), **kwargs)

    def to_internal_value(self, data):
        if isinstance(data, str) and not data.isdigit():
            try:
                return ContentType.objects.get(model=data)
            except ContentType.DoesNotExist as exc:
                raise serializers.ValidationError(f"Unknown content type: {data}") from exc
        return super().to_internal_value(data)

    def to_representation(self, value):
        if value is None:
            return None
        return value.pk
