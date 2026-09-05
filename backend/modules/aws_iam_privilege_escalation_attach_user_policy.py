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
from apps.enrichments.models import EnrichmentProvider, EnrichmentType


class Module(BaseModule):
    NAME = "AWS IAM Privilege Escalation via AttachUserPolicy"
    DESC = "Detects AWS IAM AttachUserPolicy activity that may grant privilege escalation."
    STREAM_NAME = "Cloud-01-AWS-IAM-Privilege-Escalation-via-AttachUserPolicy"

    def run(self, message):
        if not isinstance(message, dict):
            raise ValueError("AWS IAM module expects a dict message.")

        event_time, time_unmapped = parse_event_time(message.get("eventTime") or message.get("@timestamp"))
        event_id = message.get("eventID", "")
        aws_region = message.get("awsRegion", "")
        source_ip = message.get("sourceIPAddress", "")
        user_agent = message.get("userAgent", "")
        user_identity = message.get("userIdentity") or {}
        principal_user = user_identity.get("userName", "")
        principal_arn = user_identity.get("arn", "")
        principal_id = user_identity.get("principalId", "")
        access_key_id = user_identity.get("accessKeyId", "")
        account_id = user_identity.get("accountId", message.get("recipientAccountId", message.get("cloud.account.id", "")))
        request_params = message.get("requestParameters") or {}
        target_user = request_params.get("userName", "")
        policy_arn = request_params.get("policyArn", "")
        policy_name = policy_arn.split("/")[-1] if policy_arn else "UnknownPolicy"
        error_code = message.get("errorCode")
        error_message = message.get("errorMessage")
        outcome = message.get("event.outcome", "")

        if not any([principal_user, target_user, account_id]):
            raise ValueError("AWS IAM module requires at least one principal, target user, or account id.")

        risk_score = _float_value(message.get("event.risk_score", 80), 80.0)
        risk_level = _risk_level(risk_score)
        severity = _severity_from_log_level(message.get("log.level", "warning"))
        disposition, action = _disposition_action(error_code)

        correlation_uid = generate_correlation_uid(
            rule_id=self.STREAM_NAME,
            time_window="24h",
            keys=[account_id, principal_user, target_user],
            timestamp=event_time,
        )

        artifacts = _artifacts(
            principal_user=principal_user,
            principal_arn=principal_arn,
            principal_id=principal_id,
            access_key_id=access_key_id,
            target_user=target_user,
            source_ip=source_ip,
            user_agent=user_agent,
            policy_arn=policy_arn,
            account_id=account_id,
        )
        enrichments = []
        if aws_region:
            enrichments.append(
                {
                    "name": "AWS Region",
                    "type": EnrichmentType.GEO_LOCATION,
                    "provider": EnrichmentProvider.AWS_CLOUDTRAIL,
                    "value": aws_region,
                    "desc": "Alert region from raw CloudTrail event",
                    "data": {"awsRegion": aws_region},
                }
            )

        unmapped = {
            **time_unmapped,
            "errorCode": error_code,
            "errorMessage": error_message,
            "awsRegion": aws_region,
            "principalId": principal_id,
            "requestID": message.get("requestID"),
        }

        return create_alert_with_context(
            case_defaults={
                "title": f"IAM Privilege Escalation: {principal_user or 'unknown'} -> {target_user or 'unknown'} in Account {account_id or 'unknown'}",
                "severity": severity,
                "impact": CaseImpact.CRITICAL if outcome == "success" else CaseImpact.MEDIUM,
                "priority": CasePriority.HIGH if outcome == "success" else CasePriority.MEDIUM,
                "confidence": CaseConfidence.HIGH,
                "description": f"Investigation required for AttachUserPolicy activity by {principal_user or 'unknown'} targeting {target_user or 'unknown'} in account {account_id or 'unknown'}.",
                "category": ProductCategory.CLOUD,
                "tags": ["iam", "aws", "privesc"],
                "correlation_uid": correlation_uid,
            },
            alert_fields={
                "title": f"AWS IAM PrivEsc: {principal_user or 'unknown'} attached {policy_name} to {target_user or 'unknown'}",
                "severity": severity,
                "status": AlertStatus.NEW,
                "status_detail": f"Outcome: {outcome}",
                "disposition": disposition,
                "action": action,
                "rule_id": self.STREAM_NAME,
                "rule_name": self.NAME,
                "source_uid": event_id,
                "correlation_uid": correlation_uid,
                "analytic_type": AlertAnalyticType.RULE,
                "analytic_name": "CloudTrail IAM Security Rule",
                "analytic_desc": "Detects AttachUserPolicy API calls that can grant privilege escalation.",
                "product_category": ProductCategory.CLOUD,
                "product_name": "AWS CloudTrail",
                "product_vendor": "Amazon AWS",
                "product_feature": "IAM Auditing",
                "first_seen_time": event_time,
                "last_seen_time": event_time,
                "desc": f"User {principal_user or 'unknown'} initiated AttachUserPolicy for {target_user or 'unknown'}. Policy: {policy_arn or 'N/A'}. Source IP: {source_ip or 'N/A'}.",
                "data_sources": ["aws.cloudtrail"],
                "labels": ["aws", "iam", "privilege-escalation", f"account:{account_id}", outcome],
                "raw_data": message,
                "unmapped": unmapped,
                "tactic": "Privilege Escalation",
                "technique": "T1098 - Account Manipulation",
                "sub_technique": "T1098.003 - Additional Cloud Credentials",
                "mitigation": "Implement least privilege, permission boundaries, and monitoring for sensitive IAM API calls.",
                "policy_type": AlertPolicyType.IDENTITY_POLICY,
                "impact": Impact.CRITICAL if outcome == "success" else Impact.MEDIUM,
                "confidence": Confidence.HIGH,
                "risk_level": risk_level,
            },
            artifacts=artifacts,
            enrichments=enrichments,
            schedule_analysis=True,
            analysis_trigger=self.STREAM_NAME,
        )


def _float_value(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _risk_level(score):
    if score >= 90:
        return AlertRiskLevel.CRITICAL
    if score >= 70:
        return AlertRiskLevel.HIGH
    if score >= 40:
        return AlertRiskLevel.MEDIUM
    return AlertRiskLevel.LOW


def _severity_from_log_level(log_level):
    return {
        "critical": Severity.CRITICAL,
        "error": Severity.HIGH,
        "warning": Severity.HIGH,
        "info": Severity.LOW,
    }.get(str(log_level).lower(), Severity.HIGH)


def _disposition_action(error_code):
    if error_code == "UnauthorizedOperation":
        return Disposition.UNAUTHORIZED, AlertAction.DENIED
    if error_code:
        return Disposition.ERROR, AlertAction.OTHER
    return Disposition.DETECTED, AlertAction.MODIFIED


def _artifacts(**values):
    specs = [
        ("principal_user", ArtifactType.USER_NAME, ArtifactRole.ACTOR, ArtifactName.PRINCIPAL_USER),
        ("principal_arn", ArtifactType.RESOURCE_UID, ArtifactRole.ACTOR, ArtifactName.CLOUD_RESOURCE_ARN),
        ("principal_id", ArtifactType.RESOURCE_UID, ArtifactRole.ACTOR, ArtifactName.CLOUD_RESOURCE_ID),
        ("access_key_id", ArtifactType.USER_CREDENTIAL_ID, ArtifactRole.ACTOR, ArtifactName.ACCESS_KEY_ID),
        ("target_user", ArtifactType.USER_NAME, ArtifactRole.TARGET, ArtifactName.TARGET_USER),
        ("source_ip", ArtifactType.IP_ADDRESS, ArtifactRole.ACTOR, ArtifactName.SOURCE_IP),
        ("user_agent", ArtifactType.HTTP_USER_AGENT, ArtifactRole.OTHER, ArtifactName.HTTP_USER_AGENT),
        ("policy_arn", ArtifactType.RESOURCE_UID, ArtifactRole.RELATED, ArtifactName.IAM_POLICY_ARN),
        ("account_id", ArtifactType.ACCOUNT, ArtifactRole.AFFECTED, ArtifactName.AWS_ACCOUNT_ID),
    ]
    artifacts = []
    for key, type_, role, name in specs:
        value = values.get(key)
        if value:
            artifacts.append({"type": type_, "role": role, "value": value, "name": name})
    return artifacts
