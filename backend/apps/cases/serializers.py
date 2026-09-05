from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import serializers

from apps.inbox.notifications import notify_case_assignment
from .models import Case, CaseRelationship, CaseRelationshipType, CaseStatus
from .services import case_summary, validate_relationship


class CaseDetailSerializer(serializers.ModelSerializer):
    assignee_name = serializers.SerializerMethodField()
    first_alert_seen_time = serializers.SerializerMethodField()
    detection_time_seconds = serializers.SerializerMethodField()
    acknowledgement_time_seconds = serializers.SerializerMethodField()
    response_time_seconds = serializers.SerializerMethodField()
    relationship_count = serializers.IntegerField(read_only=True, default=0)

    def _get_user_name(self, user):
        if not user:
            return ""
        return user.get_full_name() or user.username

    def get_assignee_name(self, obj):
        return self._get_user_name(obj.assignee)

    def _duration_seconds(self, start, end):
        if not start or not end:
            return None
        return int((end - start).total_seconds())

    def _first_alert_seen_time(self, obj):
        annotated_value = getattr(obj, "first_alert_seen_time", None)
        if annotated_value is not None:
            return annotated_value
        return obj.alerts.filter(first_seen_time__isnull=False).order_by("first_seen_time").values_list("first_seen_time", flat=True).first()

    def get_first_alert_seen_time(self, obj):
        value = self._first_alert_seen_time(obj)
        if value is None:
            return None
        return serializers.DateTimeField().to_representation(value)

    def get_detection_time_seconds(self, obj):
        return self._duration_seconds(self._first_alert_seen_time(obj), obj.created_at)

    def get_acknowledgement_time_seconds(self, obj):
        return self._duration_seconds(obj.created_at, obj.acknowledged_time)

    def get_response_time_seconds(self, obj):
        return self._duration_seconds(obj.acknowledged_time, obj.closed_time)

    def update(self, instance, validated_data):
        previous_assignee_id = instance.assignee_id
        previous_status = instance.status or ""
        next_status = validated_data.get("status", previous_status) or ""
        status_changed = next_status != previous_status
        now = timezone.now()

        if (
            status_changed
            and previous_status in ("", CaseStatus.NEW)
            and next_status != CaseStatus.NEW
            and not instance.acknowledged_time
            and "acknowledged_time" not in validated_data
        ):
            validated_data["acknowledged_time"] = now

        if (
            status_changed
            and next_status == CaseStatus.CLOSED
            and not instance.closed_time
            and "closed_time" not in validated_data
        ):
            validated_data["closed_time"] = now

        updated = super().update(instance, validated_data)
        request = self.context.get("request")
        actor = getattr(request, "user", None) if request else None
        notify_case_assignment(updated, previous_assignee_id=previous_assignee_id, actor=actor)
        return updated

    class Meta:
        model = Case
        fields = (
            "id",
            "case_id",
            "title",
            "severity",
            "impact",
            "priority",
            "confidence",
            "description",
            "category",
            "tags",
            "status",
            "verdict",
            "summary",
            "assignee",
            "assignee_name",
            "acknowledged_time",
            "closed_time",
            "correlation_uid",
            "severity_ai",
            "confidence_ai",
            "impact_ai",
            "priority_ai",
            "verdict_ai",
            "first_alert_seen_time",
            "detection_time_seconds",
            "acknowledgement_time_seconds",
            "response_time_seconds",
            "relationship_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "case_id", "created_at", "updated_at")


class CaseListSerializer(CaseDetailSerializer):
    alert_count = serializers.IntegerField(read_only=True, default=0)
    playbook_count = serializers.IntegerField(read_only=True, default=0)
    enrichment_count = serializers.IntegerField(read_only=True, default=0)

    class Meta(CaseDetailSerializer.Meta):
        fields = (
            "id",
            "case_id",
            "title",
            "severity",
            "impact",
            "priority",
            "confidence",
            "description",
            "category",
            "tags",
            "status",
            "verdict",
            "summary",
            "assignee",
            "assignee_name",
            "acknowledged_time",
            "closed_time",
            "correlation_uid",
            "severity_ai",
            "confidence_ai",
            "impact_ai",
            "priority_ai",
            "verdict_ai",
            "alert_count",
            "playbook_count",
            "enrichment_count",
            "first_alert_seen_time",
            "detection_time_seconds",
            "acknowledgement_time_seconds",
            "response_time_seconds",
            "relationship_count",
            "created_at",
            "updated_at",
        )


class CaseRelationshipSerializer(serializers.ModelSerializer):
    source_case_id = serializers.PrimaryKeyRelatedField(
        source="source_case",
        queryset=Case.objects.all(),
        write_only=True,
    )
    target_case_id = serializers.PrimaryKeyRelatedField(
        source="target_case",
        queryset=Case.objects.all(),
        write_only=True,
    )
    source_case = serializers.SerializerMethodField()
    target_case = serializers.SerializerMethodField()
    created_by = serializers.CharField(source="created_by.username", read_only=True, default="")

    class Meta:
        model = CaseRelationship
        fields = (
            "id",
            "source_case_id",
            "target_case_id",
            "source_case",
            "target_case",
            "relationship_type",
            "note",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
        extra_kwargs = {
            "note": {"allow_blank": True, "max_length": 500},
        }

    def get_source_case(self, obj):
        return case_summary(obj.source_case)

    def get_target_case(self, obj):
        return case_summary(obj.target_case)

    def validate(self, attrs):
        source_case = attrs.get("source_case", getattr(self.instance, "source_case", None))
        target_case = attrs.get("target_case", getattr(self.instance, "target_case", None))
        relationship_type = attrs.get(
            "relationship_type",
            getattr(self.instance, "relationship_type", None),
        )
        if source_case is None:
            raise serializers.ValidationError({"source_case_id": ["This field is required."]})
        if target_case is None:
            raise serializers.ValidationError({"target_case_id": ["This field is required."]})
        if self.instance and {
            source_case.id,
            target_case.id,
        } != {
            self.instance.source_case_id,
            self.instance.target_case_id,
        }:
            raise serializers.ValidationError(
                {"target_case_id": ["The related Case cannot be changed."]}
            )

        if relationship_type == CaseRelationshipType.RELATED and str(source_case.id) > str(target_case.id):
            source_case, target_case = target_case, source_case
            attrs["source_case"] = source_case
            attrs["target_case"] = target_case

        validate_relationship(
            source_case,
            target_case,
            relationship_type,
            getattr(self.instance, "id", None),
        )
        return attrs

    def _locked_cases(self, source_case, target_case):
        case_ids = sorted((source_case.id, target_case.id), key=str)
        locked = {
            case.id: case
            for case in Case.objects.select_for_update().filter(pk__in=case_ids)
        }
        return locked[source_case.id], locked[target_case.id]

    @transaction.atomic
    def create(self, validated_data):
        source_case, target_case = self._locked_cases(
            validated_data["source_case"],
            validated_data["target_case"],
        )
        validate_relationship(
            source_case,
            target_case,
            validated_data["relationship_type"],
        )
        request = self.context.get("request")
        validated_data["source_case"] = source_case
        validated_data["target_case"] = target_case
        validated_data["created_by"] = (
            request.user if request and request.user.is_authenticated else None
        )
        try:
            return super().create(validated_data)
        except IntegrityError as exc:
            raise serializers.ValidationError(
                {"detail": ["The relationship conflicts with an existing relationship."]}
            ) from exc

    @transaction.atomic
    def update(self, instance, validated_data):
        source_case = validated_data.get("source_case", instance.source_case)
        target_case = validated_data.get("target_case", instance.target_case)
        source_case, target_case = self._locked_cases(source_case, target_case)
        relationship_type = validated_data.get("relationship_type", instance.relationship_type)
        validate_relationship(source_case, target_case, relationship_type, instance.id)
        validated_data["source_case"] = source_case
        validated_data["target_case"] = target_case
        try:
            return super().update(instance, validated_data)
        except IntegrityError as exc:
            raise serializers.ValidationError(
                {"detail": ["The relationship conflicts with an existing relationship."]}
            ) from exc
