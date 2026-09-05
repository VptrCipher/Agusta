from collections import defaultdict

from django.db import OperationalError, connection, transaction
from django.db.models import Count, Max, Q, Subquery
from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError

from apps.alerts.models import Alert
from apps.artifacts.models import Artifact

from .models import Case, CaseRelationship, CaseRelationshipType

SUGGESTION_ARTIFACT_LIMIT = 20
SUGGESTION_QUERY_TIMEOUT_MS = 3000


class SuggestionQueryTimeout(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Case relationship suggestions timed out because the dataset is too large."
    default_code = "suggestion_query_timeout"


def case_summary(case):
    return {
        "id": str(case.id),
        "case_id": case.case_id,
        "title": case.title,
        "status": case.status,
        "severity": case.severity,
        "verdict": case.verdict,
        "assignee_id": case.assignee_id,
        "assignee_name": (
            case.assignee.get_full_name() or case.assignee.username
            if case.assignee_id
            else ""
        ),
    }


def relationships_for_case(case):
    return (
        CaseRelationship.objects
        .filter(Q(source_case=case) | Q(target_case=case))
        .select_related("source_case__assignee", "target_case__assignee", "created_by")
        .order_by("-created_at")
    )


def relationship_for_case_payload(relationship, case):
    is_source = relationship.source_case_id == case.id
    related_case = relationship.target_case if is_source else relationship.source_case
    if relationship.relationship_type == CaseRelationshipType.RELATED:
        relation = CaseRelationshipType.RELATED
    elif relationship.relationship_type == CaseRelationshipType.DUPLICATE_OF:
        relation = "Duplicate of" if is_source else "Has duplicate"
    else:
        relation = "Parent of" if is_source else "Child of"
    return {
        "id": str(relationship.id),
        "relationship_type": relationship.relationship_type,
        "relation": relation,
        "related_case": case_summary(related_case),
        "note": relationship.note,
        "created_by": relationship.created_by.username if relationship.created_by else "",
        "created_at": relationship.created_at.isoformat(),
        "updated_at": relationship.updated_at.isoformat(),
    }


def _excluding(queryset, relationship_id):
    if relationship_id:
        return queryset.exclude(pk=relationship_id)
    return queryset


def _validate_parent_relationship(source_case, target_case, relationship_id):
    existing_parent = _excluding(
        CaseRelationship.objects.filter(
            relationship_type=CaseRelationshipType.PARENT_OF,
            target_case=target_case,
        ),
        relationship_id,
    )
    if existing_parent.exists():
        raise ValidationError({"target_case_id": ["This Case already has a parent."]})

    current_id = source_case.id
    visited = set()
    while current_id and current_id not in visited:
        if current_id == target_case.id:
            raise ValidationError({"target_case_id": ["Parent relationships cannot form a cycle."]})
        visited.add(current_id)
        parent_id = (
            _excluding(
                CaseRelationship.objects.filter(
                    relationship_type=CaseRelationshipType.PARENT_OF,
                    target_case_id=current_id,
                ),
                relationship_id,
            )
            .values_list("source_case_id", flat=True)
            .first()
        )
        current_id = parent_id


def _validate_duplicate_relationship(source_case, target_case, relationship_id):
    source_duplicates = _excluding(
        CaseRelationship.objects.filter(
            relationship_type=CaseRelationshipType.DUPLICATE_OF,
            source_case=source_case,
        ),
        relationship_id,
    )
    if source_duplicates.exists():
        raise ValidationError({"source_case_id": ["This Case already has a canonical Case."]})

    target_is_duplicate = _excluding(
        CaseRelationship.objects.filter(
            relationship_type=CaseRelationshipType.DUPLICATE_OF,
            source_case=target_case,
        ),
        relationship_id,
    )
    if target_is_duplicate.exists():
        raise ValidationError({"target_case_id": ["The canonical Case cannot itself be a duplicate."]})

    source_is_canonical = _excluding(
        CaseRelationship.objects.filter(
            relationship_type=CaseRelationshipType.DUPLICATE_OF,
            target_case=source_case,
        ),
        relationship_id,
    )
    if source_is_canonical.exists():
        raise ValidationError({"source_case_id": ["A canonical Case cannot become a duplicate."]})


def validate_relationship(source_case, target_case, relationship_type, relationship_id=None):
    if source_case.id == target_case.id:
        raise ValidationError({"target_case_id": ["A Case cannot be related to itself."]})

    pair_key = CaseRelationship.build_pair_key(source_case.id, target_case.id)
    same_pair = _excluding(
        CaseRelationship.objects.filter(pair_key=pair_key),
        relationship_id,
    )
    if same_pair.exists():
        raise ValidationError({"target_case_id": ["These Cases already have a relationship."]})

    if relationship_type == CaseRelationshipType.PARENT_OF:
        _validate_parent_relationship(source_case, target_case, relationship_id)
    elif relationship_type == CaseRelationshipType.DUPLICATE_OF:
        _validate_duplicate_relationship(source_case, target_case, relationship_id)


def _suggest_related_cases(case, limit):
    source_artifact_ids = (
        Alert.artifacts.through.objects
        .filter(alert__case=case)
        .values("artifact_id")
        .annotate(last_link_id=Max("id"))
        .order_by("-last_link_id")
        .values("artifact_id")[:SUGGESTION_ARTIFACT_LIMIT]
    )
    related_case_ids = set()
    for source_case_id, target_case_id in (
        CaseRelationship.objects
        .filter(Q(source_case=case) | Q(target_case=case))
        .values_list("source_case_id", "target_case_id")
    ):
        related_case_ids.add(source_case_id)
        related_case_ids.add(target_case_id)

    candidates = list(
        Case.objects
        .select_related("assignee")
        .exclude(pk__in=related_case_ids | {case.id})
        .filter(alerts__artifacts__id__in=Subquery(source_artifact_ids))
        .annotate(
            shared_artifact_count=Count(
                "alerts__artifacts",
                filter=Q(alerts__artifacts__id__in=Subquery(source_artifact_ids)),
                distinct=True,
            )
        )
        .order_by("-shared_artifact_count", "-updated_at", "id")[:limit]
    )

    evidence_by_case = defaultdict(list)
    for candidate in candidates:
        evidence_by_case[candidate.id] = list(
            Artifact.objects
            .filter(
                id__in=Subquery(source_artifact_ids),
                alerts__case=candidate,
            )
            .order_by("type", "value", "id")
            .values("id", "type", "value")
            .distinct()[:3]
        )

    return [
        {
            "case": case_summary(candidate),
            "shared_artifact_count": candidate.shared_artifact_count,
            "shared_artifacts": [
                {
                    "id": str(artifact["id"]),
                    "type": artifact["type"],
                    "value": artifact["value"],
                }
                for artifact in evidence_by_case[candidate.id]
            ],
        }
        for candidate in candidates
    ]


def suggest_related_cases(case, limit=10):
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT set_config('statement_timeout', %s, true)",
                    [f"{SUGGESTION_QUERY_TIMEOUT_MS}ms"],
                )
            return _suggest_related_cases(case, limit)
    except OperationalError as exc:
        cause = exc.__cause__
        if (
            getattr(cause, "sqlstate", None) == "57014"
            or getattr(cause, "pgcode", None) == "57014"
        ):
            raise SuggestionQueryTimeout() from exc
        raise
