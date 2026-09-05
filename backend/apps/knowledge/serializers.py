from rest_framework import serializers

from .models import Knowledge, KnowledgeSource


class KnowledgeSerializer(serializers.ModelSerializer):
    case_readable_id = serializers.SerializerMethodField()

    def get_case_readable_id(self, obj):
        return obj.case.case_id if obj.case_id and obj.case else ""

    class Meta:
        model = Knowledge
        fields = (
            "id",
            "id",
            "created_at",
            "updated_at",
            "knowledge_id",
            "title",
            "body",
            "expires_at",
            "source",
            "tags",
            "case",
            "case_readable_id",
        )
        read_only_fields = ("id", "knowledge_id", "created_at", "updated_at", "source", "case", "case_readable_id")

    def validate(self, attrs):
        if self.instance is None and not str(attrs.get("title", "")).strip():
            raise serializers.ValidationError({"title": "Title is required."})
        return attrs

    def create(self, validated_data):
        validated_data["source"] = KnowledgeSource.MANUAL
        return super().create(validated_data)
