import hashlib
from dataclasses import dataclass

from django.db import connection, transaction

from apps.agentic.services.artifacts import get_or_create_artifact
from apps.agentic.services.cases import request_case_analysis
from apps.alerts.models import Alert
from apps.cases.models import Case
from apps.enrichments.models import Enrichment


@dataclass(frozen=True)
class AlertContextResult:
    case: Case
    alert: Alert


def _correlation_uid_lock_id(correlation_uid):
    digest = hashlib.sha256(correlation_uid.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=False) & ((1 << 63) - 1)


def _lock_case_correlation_uid(correlation_uid):
    if not correlation_uid:
        return

    lock_id = _correlation_uid_lock_id(correlation_uid)
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [lock_id])


def _get_or_create_case(case_defaults, correlation_uid):
    if correlation_uid:
        existing = Case.objects.filter(correlation_uid=correlation_uid).order_by("created_at").first()
        if existing:
            return existing
    case = Case(**case_defaults)
    case.full_clean()
    case.save()
    return case


@transaction.atomic
def create_alert_with_context(
    *,
    case_defaults,
    alert_fields,
    artifacts,
    enrichments,
    schedule_analysis=True,
    analysis_trigger="alert_created",
):
    case_defaults = dict(case_defaults)
    alert_fields = dict(alert_fields)

    case_correlation_uid = case_defaults.get("correlation_uid", "")
    alert_correlation_uid = alert_fields.get("correlation_uid", "")
    if case_correlation_uid and alert_correlation_uid and case_correlation_uid != alert_correlation_uid:
        raise ValueError("case_defaults.correlation_uid and alert_fields.correlation_uid must match")

    correlation_uid = alert_correlation_uid or case_correlation_uid
    if correlation_uid:
        case_defaults["correlation_uid"] = correlation_uid
        alert_fields["correlation_uid"] = correlation_uid

    with transaction.atomic():
        _lock_case_correlation_uid(correlation_uid)
        case = _get_or_create_case(case_defaults, correlation_uid)
        alert = Alert(case=case, **alert_fields)
        alert.full_clean()
        alert.save()

        for artifact_fields in artifacts:
            artifact = get_or_create_artifact(**artifact_fields)
            alert.artifacts.add(artifact)

        for enrichment_fields in enrichments:
            enrichment = Enrichment(alert=alert, **enrichment_fields)
            enrichment.full_clean()
            enrichment.save()

        if schedule_analysis:
            request_case_analysis(case=case, trigger=analysis_trigger)

    return AlertContextResult(case=case, alert=alert)
