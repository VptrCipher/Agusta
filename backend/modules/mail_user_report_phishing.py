import re

from apps.agentic.runtime.base import BaseModule, parse_event_time, generate_correlation_uid
from apps.agentic.services.alerts import create_alert_with_context
from apps.alerts.models import (
    AlertAction,
    AlertAnalyticType,
    AlertRiskLevel,
    AlertStatus,
    Confidence,
    Disposition,
    Impact,
    ProductCategory,
    Severity,
)
from apps.artifacts.models import ArtifactName, ArtifactRole, ArtifactType
from apps.cases.models import CaseConfidence, CaseImpact, CasePriority

EMAIL_RE = re.compile(r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})")
URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)


class Module(BaseModule):
    NAME = "User Reported Phishing Mail"
    DESC = "Creates phishing investigation cases from user-reported suspicious mail."
    STREAM_NAME = "Mail-01-User-Report-Phishing-Mail"

    def run(self, message):
        if not isinstance(message, dict):
            raise ValueError("Mail phishing module expects a dict message.")

        headers = message.get("headers", {}) or {}
        sender = _email(message.get("sender") or _header(headers, "From"))
        recipient = _email(message.get("recipient") or _header(headers, "To"))
        reporter = _email(message.get("reporter") or message.get("user.email", ""))
        subject = message.get("subject") or _header(headers, "Subject")
        message_id = message.get("message_id") or message.get("email.message_id", "")
        event_time, time_unmapped = parse_event_time(message.get("eventTime") or message.get("@timestamp") or _header(headers, "Date"))
        urls = _list_values(message.get("urls") or message.get("email.urls")) or _urls(message.get("body", ""))
        domains = _list_values(message.get("domains")) or [_domain_from_url(url) for url in urls if _domain_from_url(url)]
        attachments = message.get("attachments", []) or []

        if not sender and not subject and not urls:
            raise ValueError("Mail phishing module requires sender, subject, or URL.")

        risk_score = _float_value(message.get("event.risk_score", 60), 60.0)
        severity = Severity.HIGH if risk_score >= 70 else Severity.MEDIUM
        risk_level = AlertRiskLevel.HIGH if risk_score >= 70 else AlertRiskLevel.MEDIUM
        first_domain = domains[0] if domains else ""
        sender_domain = sender.split("@", 1)[1] if "@" in sender else ""
        normalized_subject = " ".join(subject.lower().split()) if subject else ""
        correlation_uid = generate_correlation_uid(
            rule_id=self.STREAM_NAME,
            time_window="24h",
            keys=[sender_domain, normalized_subject, first_domain],
            timestamp=event_time,
        )
        artifacts = _artifacts(sender, recipient, reporter, subject, message_id, urls, domains, attachments)

        return create_alert_with_context(
            case_defaults={
                "title": f"Phishing report: {subject or sender or 'suspicious mail'}",
                "severity": severity,
                "impact": CaseImpact.HIGH if risk_score >= 70 else CaseImpact.MEDIUM,
                "priority": CasePriority.HIGH if risk_score >= 70 else CasePriority.MEDIUM,
                "confidence": CaseConfidence.HIGH if urls else CaseConfidence.MEDIUM,
                "description": f"User-reported suspicious email from {sender or 'unknown sender'} to {recipient or 'unknown recipient'}.",
                "category": ProductCategory.EMAIL,
                "tags": ["phishing", "email", "user-report"],
                "correlation_uid": correlation_uid,
            },
            alert_fields={
                "title": f"User reported phishing: {subject or sender or 'suspicious mail'}",
                "severity": severity,
                "confidence": Confidence.HIGH if urls else Confidence.MEDIUM,
                "impact": Impact.HIGH if risk_score >= 70 else Impact.MEDIUM,
                "disposition": Disposition.DETECTED,
                "action": AlertAction.OBSERVED,
                "status": AlertStatus.NEW,
                "status_detail": f"Reporter: {reporter or 'unknown'}",
                "rule_id": self.STREAM_NAME,
                "rule_name": self.NAME,
                "source_uid": message_id,
                "correlation_uid": correlation_uid,
                "analytic_type": AlertAnalyticType.RULE,
                "analytic_name": "User Reported Phishing Mail",
                "analytic_desc": "Processes user-reported suspicious email messages.",
                "product_category": ProductCategory.EMAIL,
                "product_name": "Mail Security",
                "product_vendor": "Internal",
                "product_feature": "User Report",
                "first_seen_time": event_time,
                "last_seen_time": event_time,
                "desc": f"Reported phishing email from {sender or 'unknown'} with subject {subject or 'unknown'}.",
                "data_sources": ["email.user_report"],
                "labels": ["phishing", "email", "user-report"],
                "raw_data": message,
                "unmapped": {**time_unmapped, "domains": domains, "attachment_count": len(attachments)},
                "risk_level": risk_level,
            },
            artifacts=artifacts,
            enrichments=[],
            schedule_analysis=True,
            analysis_trigger=self.STREAM_NAME,
        )


def _header(headers, name):
    return headers.get(name, headers.get(name.lower(), ""))


def _email(value):
    if not value:
        return ""
    match = EMAIL_RE.search(str(value))
    return (match.group(1) if match else str(value)).strip().lower()


def _urls(value):
    # Mail bodies arrive either as a plain string or as a structured object with
    # separate plain_text / html parts, so accept both.
    if isinstance(value, dict):
        value = " ".join(part for part in value.values() if isinstance(part, str))
    elif not isinstance(value, str):
        value = ""
    return URL_RE.findall(value)


def _list_values(value):
    if not value:
        return []
    if isinstance(value, str):
        return [value]
    return [item for item in value if item]


def _domain_from_url(url):
    return re.sub(r"^https?://", "", url, flags=re.IGNORECASE).split("/", 1)[0].split("?", 1)[0].lower()


def _float_value(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _artifacts(sender, recipient, reporter, subject, message_id, urls, domains, attachments):
    artifacts = []
    for value, type_, role, name in [
        (sender, ArtifactType.EMAIL_ADDRESS, ArtifactRole.ACTOR, ArtifactName.SENDER_EMAIL),
        (recipient, ArtifactType.EMAIL_ADDRESS, ArtifactRole.AFFECTED, ArtifactName.RECIPIENT_EMAIL),
        (reporter, ArtifactType.EMAIL_ADDRESS, ArtifactRole.ACTOR, ArtifactName.USER_EMAIL),
        (subject, ArtifactType.MESSAGE, ArtifactRole.RELATED, ArtifactName.MAIL_SUBJECT),
        (message_id, ArtifactType.RESOURCE_UID, ArtifactRole.RELATED, ArtifactName.MAIL_MESSAGE_ID),
    ]:
        if value:
            artifacts.append({"value": value, "type": type_, "role": role, "name": name})
    for url in urls:
        artifacts.append({"value": url, "type": ArtifactType.URL_STRING, "role": ArtifactRole.RELATED, "name": ArtifactName.PHISHING_URL})
    for domain in domains:
        artifacts.append({"value": domain, "type": ArtifactType.HOSTNAME, "role": ArtifactRole.RELATED, "name": ArtifactName.DOMAIN})
    for attachment in attachments:
        filename = attachment.get("filename", "") if isinstance(attachment, dict) else str(attachment)
        sha256 = attachment.get("sha256", "") if isinstance(attachment, dict) else ""
        if filename:
            artifacts.append({"value": filename, "type": ArtifactType.FILE_NAME, "role": ArtifactRole.RELATED, "name": ArtifactName.MAIL_ATTACHMENT})
        if sha256:
            artifacts.append({"value": sha256, "type": ArtifactType.HASH, "role": ArtifactRole.RELATED, "name": ArtifactName.FILE_HASH})
    return artifacts
