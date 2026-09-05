from rest_framework import serializers
from django.utils import timezone

from .models import Playbook, PlaybookJobStatus, PlaybookRunMessage


class PlaybookSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True, default="")
    case_title = serializers.CharField(source="case.title", read_only=True)
    case_id = serializers.UUIDField(source="case.id", read_only=True)
    case_readable_id = serializers.CharField(source="case.case_id", read_only=True)
    duration_seconds = serializers.SerializerMethodField()

    def get_duration_seconds(self, obj):
        if obj.started_at is None:
            return None
        if obj.finished_at is not None:
            end = obj.finished_at
        elif obj.job_status == PlaybookJobStatus.RUNNING:
            end = timezone.now()
        else:
            return None
        return max(0, int((end - obj.started_at).total_seconds()))

    class Meta:
        model = Playbook
        fields = (
            "id",
            "playbook_id",
            "case",
            "case_id",
            "case_readable_id",
            "case_title",
            "name",
            "user_input",
            "user",
            "user_username",
            "job_status",
            "job_id",
            "started_at",
            "finished_at",
            "duration_seconds",
            "remark",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class PlaybookRunMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaybookRunMessage
        fields = ("id", "sequence", "message", "created_at")
        read_only_fields = fields
