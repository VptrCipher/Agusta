from apps.agentic.runtime.base import BaseModule, parse_event_time, generate_correlation_uid
from apps.agentic.services.alerts import create_alert_with_context
from apps.alerts.models import (
    AlertAction,
    AlertAnalyticType,
    AlertPolicyType,
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


class Module(BaseModule):
    NAME = "EDR Vssadmin Delete Shadows"
    DESC = "Detects vssadmin.exe deleting shadow copies, a ransomware precursor behavior."
    STREAM_NAME = "EDR-01-HOST-Vssadmin-Delete-Shadows"

    def run(self, message):
        if not isinstance(message, dict):
            raise ValueError("EDR Vssadmin module expects a dict message.")

        event_time, time_unmapped = parse_event_time(message.get("@timestamp") or message.get("eventTime"))
        host_name = _nested(message, "host.name", "host", "name")
        host_ip = _nested(message, "host.ip", "host", "ip")
        user_name = _nested(message, "user.name", "user", "name")
        process_name = _nested(message, "process.name", "process", "name") or "vssadmin.exe"
        command_line = _nested(message, "process.command_line", "process", "command_line")
        parent_name = _nested(message, "process.parent.name", "process", "parent", "name")
        file_path = _nested(message, "file.path", "file", "path") or _nested(message, "process.executable", "process", "executable")
        file_hash = (
            _nested(message, "file.hash.sha256", "file", "hash", "sha256")
            or _nested(message, "process.hash.sha256", "process", "hash", "sha256")
            or _nested(message, "file.hash.md5", "file", "hash", "md5")
        )

        if not host_name and not command_line:
            raise ValueError("EDR Vssadmin module requires host.name or process.command_line.")

        risk_score = _float_value(message.get("event.risk_score", message.get("risk_score", 100)), 100.0)
        risk_level = AlertRiskLevel.CRITICAL if risk_score >= 90 else AlertRiskLevel.HIGH
        severity = Severity.CRITICAL if risk_score >= 90 else Severity.HIGH
        correlation_uid = generate_correlation_uid(
            rule_id=self.STREAM_NAME,
            time_window="24h",
            keys=[host_name, user_name, command_line or process_name],
            timestamp=event_time,
        )

        artifacts = _artifacts(host_name, host_ip, user_name, process_name, command_line, parent_name, file_path, file_hash)
        unmapped = {
            **time_unmapped,
            "event.id": _nested(message, "event.id", "eventID"),
            "risk_score": risk_score,
            "parent_process": parent_name,
        }

        return create_alert_with_context(
            case_defaults={
                "title": f"Potential Ransomware Activity on {host_name or 'unknown host'} by {user_name or 'unknown user'}",
                "severity": severity,
                "impact": CaseImpact.CRITICAL,
                "priority": CasePriority.CRITICAL,
                "confidence": CaseConfidence.HIGH,
                "description": f"Shadow copy deletion detected on {host_name or 'unknown host'}: {command_line or process_name}.",
                "category": ProductCategory.EDR,
                "tags": ["ransomware", "vssadmin", "shadow-copy"],
                "correlation_uid": correlation_uid,
            },
            alert_fields={
                "title": f"Shadow Copy Deletion: {user_name or 'unknown user'} ran vssadmin on {host_name or 'unknown host'}",
                "severity": severity,
                "confidence": Confidence.HIGH,
                "impact": Impact.CRITICAL,
                "disposition": Disposition.DETECTED,
                "action": AlertAction.OBSERVED,
                "status": AlertStatus.NEW,
                "status_detail": f"Parent process: {parent_name or 'unknown'}",
                "rule_id": self.STREAM_NAME,
                "rule_name": self.NAME,
                "correlation_uid": correlation_uid,
                "source_uid": _nested(message, "event.id", "eventID"),
                "analytic_type": AlertAnalyticType.RULE,
                "analytic_name": "EDR Endpoint Security Rule",
                "analytic_desc": "Detects vssadmin.exe delete shadows command.",
                "product_category": ProductCategory.EDR,
                "product_name": "EDR",
                "product_vendor": "Endpoint Security",
                "product_feature": "Process Monitoring",
                "first_seen_time": event_time,
                "last_seen_time": event_time,
                "desc": f"Command observed: {command_line or process_name}",
                "data_sources": ["endpoint.process"],
                "labels": ["ransomware", "defense-evasion", "vssadmin"],
                "raw_data": message,
                "unmapped": unmapped,
                "tactic": "Impact",
                "technique": "T1490 - Inhibit System Recovery",
                "mitigation": "Restrict vssadmin.exe usage and monitor shadow copy deletion.",
                "policy_type": AlertPolicyType.IDENTITY_POLICY,
                "risk_level": risk_level,
            },
            artifacts=artifacts,
            enrichments=[],
            schedule_analysis=True,
            analysis_trigger=self.STREAM_NAME,
        )


def _nested(data, dotted_key, *path):
    if dotted_key in data:
        return data.get(dotted_key)
    current = data
    for part in path:
        if not isinstance(current, dict):
            return ""
        current = current.get(part, {})
    return current if not isinstance(current, dict) else ""


def _float_value(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _artifacts(host_name, host_ip, user_name, process_name, command_line, parent_name, file_path, file_hash):
    specs = [
        (host_name, ArtifactType.HOSTNAME, ArtifactRole.AFFECTED, ArtifactName.AFFECTED_HOST),
        (host_ip, ArtifactType.IP_ADDRESS, ArtifactRole.AFFECTED, ArtifactName.HOST_IP),
        (user_name, ArtifactType.USER_NAME, ArtifactRole.ACTOR, ArtifactName.SOURCE_USER),
        (process_name, ArtifactType.PROCESS_NAME, ArtifactRole.RELATED, ArtifactName.PROCESS_NAME),
        (command_line, ArtifactType.COMMAND_LINE, ArtifactRole.RELATED, ArtifactName.PROCESS_COMMAND_LINE),
        (parent_name, ArtifactType.PROCESS_NAME, ArtifactRole.RELATED, ArtifactName.PARENT_PROCESS_NAME),
        (file_path, ArtifactType.FILE_PATH, ArtifactRole.RELATED, ArtifactName.FILE_PATH),
        (file_hash, ArtifactType.HASH, ArtifactRole.RELATED, ArtifactName.FILE_HASH),
    ]
    return [
        {"value": value, "type": type_, "role": role, "name": name}
        for value, type_, role, name in specs
        if value
    ]
