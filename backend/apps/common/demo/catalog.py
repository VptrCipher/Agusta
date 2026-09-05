"""Declarative catalogue for the AGUSTA demonstration environment.

This module is pure data. ``loader.py`` turns it into database rows.

Read ``provenance.py`` first: the ATT&CK/CVE references are real public data,
everything else (organisation, people, hosts, addresses, incidents) is synthetic.

Structure
---------
``ANALYSTS``  - the SOC team that appears as assignees, commenters and actors.
``ARTIFACTS`` - one shared registry of entities. Stages reference artifacts by
                key, so the *same* Artifact row is reused across cases. That is
                what makes the artifact pivot view meaningful: clicking a host
                or account shows every case it touches.
``STORIES``   - multi-stage incident narratives. Each stage becomes one Case.
``ROUTINE``   - lower-severity background noise so dashboards look like a real
                queue rather than a handful of showcase records.
"""

from datetime import timedelta

from apps.alerts.models import (
    AlertAction,
    AlertAnalyticState,
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
from apps.cases.models import (
    CaseCategory,
    CaseConfidence,
    CaseImpact,
    CasePriority,
    CaseSeverity,
    CaseStatus,
    CaseVerdict,
)
from apps.common.demo import provenance as prov


def h(value):
    return timedelta(hours=value)


def m(value):
    return timedelta(minutes=value)


def d(value):
    return timedelta(days=value)


# --------------------------------------------------------------------------- #
# SOC team
# --------------------------------------------------------------------------- #

ANALYSTS = [
    {
        "username": "alice.chen",
        "first_name": "Alice",
        "last_name": "Chen",
        "title": "L2 Analyst / Shift Lead",
    },
    {
        "username": "bob.li",
        "first_name": "Bob",
        "last_name": "Li",
        "title": "L1 Analyst",
    },
    {
        "username": "maya.singh",
        "first_name": "Maya",
        "last_name": "Singh",
        "title": "L2 Analyst / Cloud Security",
    },
    {
        "username": "liam.osullivan",
        "first_name": "Liam",
        "last_name": "O'Sullivan",
        "title": "Incident Response",
    },
    {
        "username": "automation",
        "first_name": "AGUSTA",
        "last_name": "Automation",
        "title": "Service account",
    },
]

AUTOMATION_USER = "automation"


# --------------------------------------------------------------------------- #
# Shared artifact registry: key -> (value, type, role, name)
# --------------------------------------------------------------------------- #

ARTIFACTS = {
    # ---- Story A: identities and endpoints -----------------------------------
    "user_dliu": ("d.liu", ArtifactType.USER_NAME, ArtifactRole.ACTOR, ArtifactName.SOURCE_USER),
    "email_dliu": (f"d.liu@{prov.ORG_DOMAIN}", ArtifactType.EMAIL_ADDRESS, ArtifactRole.TARGET, ArtifactName.RECIPIENT_EMAIL),
    "host_fin_wks": ("FIN-WKS-4471", ArtifactType.HOSTNAME, ArtifactRole.AFFECTED, ArtifactName.AFFECTED_HOST),
    "ip_fin_wks": (prov.internal_ip(14, 71), ArtifactType.IP_ADDRESS, ArtifactRole.AFFECTED, ArtifactName.HOST_IP),
    "host_file_srv": ("SRV-FILE-02", ArtifactType.HOSTNAME, ArtifactRole.TARGET, ArtifactName.DESTINATION_HOST),
    "ip_file_srv": (prov.internal_ip(30, 12), ArtifactType.IP_ADDRESS, ArtifactRole.TARGET, ArtifactName.DESTINATION_IP),
    "host_db_slave": ("srv-db-slave-01", ArtifactType.HOSTNAME, ArtifactRole.AFFECTED, ArtifactName.AFFECTED_HOST),
    "user_svc_backup": ("svc_backup", ArtifactType.USER_NAME, ArtifactRole.ACTOR, ArtifactName.SOURCE_USER),

    # ---- Story A: adversary infrastructure -----------------------------------
    "email_phish_sender": ("invoices@northwind-billing.example", ArtifactType.EMAIL_ADDRESS, ArtifactRole.ACTOR, ArtifactName.SENDER_EMAIL),
    "url_phish": ("https://northwind-billing.example/invoice/NW-84213.doc", ArtifactType.URL_STRING, ArtifactRole.RELATED, ArtifactName.PHISHING_URL),
    "file_lure": ("Invoice_NW-84213.docm", ArtifactType.FILE_NAME, ArtifactRole.RELATED, ArtifactName.FILE_NAME),
    "hash_lure": (prov.EICAR_MD5, ArtifactType.HASH, ArtifactRole.RELATED, ArtifactName.FILE_HASH),
    "ip_c2_primary": (prov.adversary_ip(47), ArtifactType.IP_ADDRESS, ArtifactRole.ACTOR, ArtifactName.DESTINATION_IP),
    "domain_c2_dns": ("sync.cdn-metrics.example", ArtifactType.HOSTNAME, ArtifactRole.RELATED, ArtifactName.DNS_QUERY_NAME),
    "domain_c2_http": ("update.cdn-metrics.example", ArtifactType.HOSTNAME, ArtifactRole.RELATED, ArtifactName.DOMAIN),

    # ---- Story A: on-host behaviour -----------------------------------------
    "cmd_powershell_enc": (
        "powershell.exe -nop -w hidden -enc SQBFAFgAIAAoAE4AZQB3AC0ATwBiAGoAZQBjAHQA",
        ArtifactType.COMMAND_LINE, ArtifactRole.RELATED, ArtifactName.PROCESS_COMMAND_LINE,
    ),
    "cmd_vssadmin": ("vssadmin.exe delete shadows /all /quiet", ArtifactType.COMMAND_LINE, ArtifactRole.RELATED, ArtifactName.PROCESS_COMMAND_LINE),
    "cmd_schtasks": (
        'schtasks /create /sc minute /mo 15 /tn "OneDriveSyncMaintenance" /tr "wscript.exe C:\\ProgramData\\odsync.vbs"',
        ArtifactType.COMMAND_LINE, ArtifactRole.RELATED, ArtifactName.PROCESS_COMMAND_LINE,
    ),
    "proc_rundll": ("rundll32.exe", ArtifactType.PROCESS_NAME, ArtifactRole.RELATED, ArtifactName.PROCESS_NAME),
    "proc_winword": ("WINWORD.EXE", ArtifactType.PROCESS_NAME, ArtifactRole.RELATED, ArtifactName.PARENT_PROCESS_NAME),
    "proc_vssadmin": ("vssadmin.exe", ArtifactType.PROCESS_NAME, ArtifactRole.RELATED, ArtifactName.PROCESS_NAME),
    "file_persist": ("C:\\ProgramData\\odsync.vbs", ArtifactType.FILE_PATH, ArtifactRole.RELATED, ArtifactName.FILE_PATH),
    "file_ransom_note": ("C:\\Users\\Public\\RESTORE-YOUR-FILES.txt", ArtifactType.FILE_PATH, ArtifactRole.RELATED, ArtifactName.FILE_PATH),
    "file_staging_archive": ("C:\\Windows\\Temp\\nw-fin-q3.7z", ArtifactType.FILE_PATH, ArtifactRole.RELATED, ArtifactName.FILE_PATH),

    # ---- Story B: cloud identity --------------------------------------------
    "user_moyelaran": ("m.oyelaran", ArtifactType.USER_NAME, ArtifactRole.ACTOR, ArtifactName.SOURCE_USER),
    "email_moyelaran": (f"m.oyelaran@{prov.ORG_DOMAIN}", ArtifactType.EMAIL_ADDRESS, ArtifactRole.ACTOR, ArtifactName.SENDER_EMAIL),
    "ip_signin_lagos": (prov.external_ip(88), ArtifactType.IP_ADDRESS, ArtifactRole.ACTOR, ArtifactName.SOURCE_IP),
    "ip_signin_vpn": (prov.adversary_ip(203), ArtifactType.IP_ADDRESS, ArtifactRole.ACTOR, ArtifactName.SOURCE_IP),
    "aws_role_audit": ("arn:aws:iam::123456789012:role/NorthwindReadOnly", ArtifactType.RESOURCE, ArtifactRole.TARGET, ArtifactName.IAM_ROLE),
    "aws_policy_admin": ("arn:aws:iam::aws:policy/AdministratorAccess", ArtifactType.RESOURCE, ArtifactRole.TARGET, ArtifactName.IAM_POLICY_ARN),
    "aws_user_ci": ("arn:aws:iam::123456789012:user/ci-deploy", ArtifactType.RESOURCE, ArtifactRole.AFFECTED, ArtifactName.IAM_USER),
    "aws_bucket_fin": ("northwind-finance-reports", ArtifactType.RESOURCE, ArtifactRole.TARGET, ArtifactName.CLOUD_BUCKET),
    "ua_awscli": ("aws-cli/2.15.30 Python/3.11.8 Linux/6.5.0", ArtifactType.HTTP_USER_AGENT, ArtifactRole.RELATED, ArtifactName.HTTP_USER_AGENT),

    # ---- Story C: insider exfiltration --------------------------------------
    "user_rkovacs": ("r.kovacs", ArtifactType.USER_NAME, ArtifactRole.ACTOR, ArtifactName.SOURCE_USER),
    "host_dev_wks": ("DEV-WKS-2210", ArtifactType.HOSTNAME, ArtifactRole.AFFECTED, ArtifactName.AFFECTED_HOST),
    "file_source_archive": ("northwind-pricing-engine-src.zip", ArtifactType.FILE_NAME, ArtifactRole.RELATED, ArtifactName.FILE_NAME),
    "url_personal_cloud": ("https://filedrop.example/u/9f31c2/upload", ArtifactType.URL_STRING, ArtifactRole.TARGET, ArtifactName.URL),
    "domain_personal_cloud": ("filedrop.example", ArtifactType.HOSTNAME, ArtifactRole.TARGET, ArtifactName.DOMAIN),

    # ---- Story D: internet-facing exploitation ------------------------------
    "host_portal": ("customer-portal.northwind.example", ArtifactType.HOSTNAME, ArtifactRole.TARGET, ArtifactName.DESTINATION_HOST),
    "ip_portal": (prov.dmz_ip(22), ArtifactType.IP_ADDRESS, ArtifactRole.TARGET, ArtifactName.DESTINATION_IP),
    "ip_attacker_scan": (prov.adversary_ip(119), ArtifactType.IP_ADDRESS, ArtifactRole.ACTOR, ArtifactName.SOURCE_IP),
    "cve_moveit": ("CVE-2023-34362", ArtifactType.CVE, ArtifactRole.RELATED, ArtifactName.CVE),
    "cwe_sqli": ("CWE-89", ArtifactType.CWE, ArtifactRole.RELATED, ArtifactName.CWE),
    "url_sqli": ("/moveitisapi/moveitisapi.dll?action=m2", ArtifactType.URL_STRING, ArtifactRole.TARGET, ArtifactName.URL),
    "ua_sqlmap": ("sqlmap/1.8.2#stable (https://sqlmap.org)", ArtifactType.HTTP_USER_AGENT, ArtifactRole.RELATED, ArtifactName.HTTP_USER_AGENT),
    "file_webshell": ("/var/www/portal/uploads/human2.aspx", ArtifactType.FILE_PATH, ArtifactRole.RELATED, ArtifactName.FILE_PATH),

    # ---- Story E: benign / authorised activity ------------------------------
    "user_redteam": ("svc_pentest", ArtifactType.USER_NAME, ArtifactRole.ACTOR, ArtifactName.SOURCE_USER),
    "host_redteam": ("REDTEAM-KALI-03", ArtifactType.HOSTNAME, ArtifactRole.ACTOR, ArtifactName.SOURCE_HOST),
    "user_sysadmin": ("a.novak", ArtifactType.USER_NAME, ArtifactRole.ACTOR, ArtifactName.SOURCE_USER),
    "host_jump": ("SRV-JUMP-01", ArtifactType.HOSTNAME, ArtifactRole.AFFECTED, ArtifactName.AFFECTED_HOST),
    "domain_doh": ("dns.quad9.net", ArtifactType.HOSTNAME, ArtifactRole.TARGET, ArtifactName.DNS_QUERY_NAME),
    "host_scanner": ("SRV-QUALYS-01", ArtifactType.HOSTNAME, ArtifactRole.ACTOR, ArtifactName.SOURCE_HOST),
    "ip_scanner": (prov.internal_ip(9, 40), ArtifactType.IP_ADDRESS, ArtifactRole.ACTOR, ArtifactName.SOURCE_IP),
}


# --------------------------------------------------------------------------- #
# Vendor mapping per product category (nominative use of real product names).
# --------------------------------------------------------------------------- #

VENDORS = {
    ProductCategory.EDR: ("CrowdStrike", "Falcon", "Process Monitoring"),
    ProductCategory.IAM: ("Okta", "Workforce Identity Cloud", "Sign-in Risk Detection"),
    ProductCategory.NDR: ("Vectra AI", "Cognito Detect", "DNS Analytics"),
    ProductCategory.EMAIL: ("Proofpoint", "Targeted Attack Protection", "Attachment Defense"),
    ProductCategory.CLOUD: ("Amazon Web Services", "CloudTrail", "IAM Auditing"),
    ProductCategory.DLP: ("Microsoft", "Purview Data Loss Prevention", "Endpoint DLP"),
    ProductCategory.WAF: ("Cloudflare", "Web Application Firewall", "Managed Ruleset"),
    ProductCategory.PROXY: ("Zscaler", "Internet Access", "Web Inspection"),
    ProductCategory.TI: ("AlienVault", "Open Threat Exchange", "IOC Matching"),
    ProductCategory.UEBA: ("Exabeam", "Advanced Analytics", "Behavioural Baseline"),
    ProductCategory.SIEM: ("Elastic", "Elastic Security", "Detection Rules"),
}


# --------------------------------------------------------------------------- #
# Incident narratives.
#
# Each story is a campaign; each stage becomes one Case with its own Alerts,
# Artifacts, Enrichments, Playbook runs and analyst discussion. Stages in a
# story with ``"chain": True`` are linked Parent of -> child in order, so the
# Case relationship view renders the kill chain.
#
# Offsets are "time ago from seeding", so the environment always looks current.
# --------------------------------------------------------------------------- #

STORIES = [
    # ======================================================================= #
    # STORY A - flagship. A full human-operated ransomware intrusion, caught
    # mid-chain. Demonstrates correlation across six products, AI triage,
    # enrichment, prioritisation and live incident handling.
    # ======================================================================= #
    {
        "key": "quiet-vault",
        "name": "Operation Quiet Vault",
        "actor": "Unattributed financially-motivated intrusion set",
        "narrative": (
            "A finance user opens a macro-enabled invoice lure. The macro stages a "
            "PowerShell loader, establishes a scheduled-task foothold, dumps LSASS to "
            "harvest a service credential, pivots to the file server over SMB and RDP, "
            "beacons out over DNS, stages a 7-Zip archive of finance data, and finally "
            "deletes volume shadow copies to prepare for encryption. AGUSTA folded "
            "eleven product alerts into six correlated cases sharing four artifacts."
        ),
        "chain": True,
        "stages": [
            {
                "key": "qv-1-initial-access",
                "title": "Macro-enabled invoice lure delivered to finance user d.liu",
                "category": CaseCategory.EMAIL,
                "severity": CaseSeverity.HIGH,
                "confidence": CaseConfidence.HIGH,
                "impact": CaseImpact.MEDIUM,
                "priority": CasePriority.HIGH,
                "status": CaseStatus.RESOLVED,
                "verdict": CaseVerdict.TRUE_POSITIVE,
                "assignee": "bob.li",
                "tags": ["phishing", "initial-access", "finance", "quiet-vault"],
                "first_seen": d(6) + h(4),
                "ttd": m(12),
                "tta": m(8),
                "ttr": h(3) + m(20),
                "description": (
                    "Mail gateway detonated a macro-enabled Word attachment sent from a "
                    "look-alike billing domain. The message reached the recipient's inbox "
                    "before the verdict returned; the attachment was opened."
                ),
                "summary": (
                    "Confirmed malicious. Sender domain blocked, message purged from the "
                    "mailbox, and the endpoint handed to EDR triage as case qv-2. "
                    "Recipient completed re-training."
                ),
                "ai": {
                    "hypothesis": "Targeted invoice-themed phishing delivering a macro loader",
                    "confidence": "High",
                    "reasoning": [
                        "Sender domain registered 6 days before delivery and typosquats the corporate billing domain.",
                        "Attachment contains an auto-executing AutoOpen macro that reaches out over HTTP.",
                        "Recipient is in the finance approval group, consistent with pre-ransomware targeting.",
                    ],
                    "recommended_actions": [
                        "Block sender domain at the gateway",
                        "Purge the message from all mailboxes",
                        "Isolate and triage the recipient endpoint",
                    ],
                },
                "alerts": [
                    {
                        "title": "Malicious attachment delivered: Invoice_NW-84213.docm",
                        "attack": "spearphishing_attachment",
                        "product": ProductCategory.EMAIL,
                        "severity": Severity.HIGH,
                        "confidence": Confidence.HIGH,
                        "impact": Impact.MEDIUM,
                        "disposition": Disposition.DELAYED,
                        "action": AlertAction.OBSERVED,
                        "status": AlertStatus.RESOLVED,
                        "risk": AlertRiskLevel.HIGH,
                        # Matches the STREAM_NAME of the bundled mail Module.
                        "rule_id": "Mail-01-User-Report-Phishing-Mail",
                        "rule_name": "User Reported Phishing Mail",
                        "analytic_type": AlertAnalyticType.BEHAVIORAL,
                        "analytic_name": "Attachment Detonation Sandbox",
                        "analytic_desc": "Detonates Office attachments and scores observed behaviour.",
                        "desc": (
                            "Sandbox detonation observed AutoOpen macro spawning an HTTP request to a "
                            "newly registered domain. Verdict returned 4 minutes after delivery."
                        ),
                        "mitigation": "Block the sender domain and purge delivered copies from all mailboxes.",
                        "labels": ["phishing", "macro", "quiet-vault"],
                        "artifacts": ["email_phish_sender", "email_dliu", "file_lure", "hash_lure", "url_phish"],
                        "offset": m(0),
                        "raw": {
                            "event.dataset": "proofpoint.tap",
                            "event.action": "message_delivered",
                            "email.from.address": "invoices@northwind-billing.example",
                            "email.subject": "Overdue invoice NW-84213 - action required",
                            "email.attachments.file.name": "Invoice_NW-84213.docm",
                            "email.attachments.file.hash.md5": prov.EICAR_MD5,
                            "sandbox.verdict": "malicious",
                            "sandbox.score": 91,
                            "note": prov.EICAR_NOTE,
                        },
                    },
                    {
                        "title": "User clicked embedded URL in quarantined phishing message",
                        "attack": "spearphishing_link",
                        "product": ProductCategory.PROXY,
                        "severity": Severity.MEDIUM,
                        "confidence": Confidence.HIGH,
                        "impact": Impact.MEDIUM,
                        "disposition": Disposition.BLOCKED,
                        "action": AlertAction.DENIED,
                        "status": AlertStatus.RESOLVED,
                        "risk": AlertRiskLevel.MEDIUM,
                        "rule_id": "ZS-URL-3302",
                        "rule_name": "Newly registered domain - credential phishing category",
                        "analytic_type": AlertAnalyticType.RULE,
                        "analytic_name": "URL Category Engine",
                        "analytic_desc": "Blocks navigation to newly registered and phishing-categorised domains.",
                        "desc": "Web proxy blocked navigation to the lure URL 3 minutes after the message was opened.",
                        "mitigation": "Confirm no credentials were submitted; reset the user's password if in doubt.",
                        "labels": ["phishing", "url-block", "quiet-vault"],
                        "artifacts": ["user_dliu", "url_phish", "host_fin_wks"],
                        "offset": m(9),
                        "raw": {
                            "event.dataset": "zscaler.web",
                            "url.full": "https://northwind-billing.example/invoice/NW-84213.doc",
                            "url.domain": "northwind-billing.example",
                            "zscaler.action": "blocked",
                            "zscaler.urlcategory": "Phishing",
                            "user.name": "d.liu",
                        },
                    },
                ],
                "enrichments": [
                    {
                        "target": "case",
                        "name": "Sender domain registration age",
                        "type": "WHOIS",
                        "provider": "DomainTools",
                        "value": "northwind-billing.example",
                        "desc": "Domain registered 6 days before the campaign; privacy-protected registrant.",
                        "data": {
                            "domain": "northwind-billing.example",
                            "created": "6 days before delivery",
                            "registrar": "(synthetic)",
                            "registrant": "REDACTED FOR PRIVACY",
                            "verdict": "suspicious - newly registered typosquat",
                        },
                    },
                    {
                        "target": "case",
                        "name": "Attachment reputation",
                        "type": "Reputation",
                        "provider": "VirusTotal",
                        "value": prov.EICAR_MD5,
                        "desc": "Hash is the published EICAR test file, used so the dataset carries no real malware.",
                        "data": {"md5": prov.EICAR_MD5, "note": prov.EICAR_NOTE},
                    },
                ],
                "comments": [
                    ("bob.li", "Verdict came back 4 min after delivery so the mail landed. Purged from the mailbox and blocked the domain. Endpoint side handed to @alice.chen.", ["alice.chen"]),
                    ("alice.chen", "Picked up. EDR already has process activity on FIN-WKS-4471, opening a linked case.", []),
                ],
                "playbooks": [
                    {
                        "name": "Threat Intelligence Enrichment",
                        "status": "Success",
                        "user": "bob.li",
                        "user_input": "Enrich sender domain and attachment hash.",
                        "remark": "3 artifacts enriched across DomainTools and VirusTotal.",
                        "started_offset": m(20),
                        "duration": m(1),
                        "messages": [
                            "Collecting artifacts for case...",
                            "DomainTools: northwind-billing.example registered 6 days ago.",
                            "VirusTotal: attachment hash matches EICAR test file.",
                            "Wrote 2 enrichment records.",
                        ],
                    },
                ],
            },
            {
                "key": "qv-2-execution",
                "title": "PowerShell loader and scheduled-task persistence on FIN-WKS-4471",
                "category": CaseCategory.EDR,
                "severity": CaseSeverity.HIGH,
                "confidence": CaseConfidence.HIGH,
                "impact": CaseImpact.HIGH,
                "priority": CasePriority.HIGH,
                "status": CaseStatus.RESOLVED,
                "verdict": CaseVerdict.TRUE_POSITIVE,
                "assignee": "alice.chen",
                "tags": ["execution", "persistence", "powershell", "quiet-vault"],
                "first_seen": d(6) + h(3) + m(10),
                "ttd": m(4),
                "tta": m(6),
                "ttr": h(5) + m(5),
                "description": (
                    "WINWORD.EXE spawned an encoded PowerShell command, which wrote a VBScript "
                    "payload and registered a 15-minute scheduled task for persistence."
                ),
                "summary": (
                    "Persistence removed, payload quarantined, host reimaged. Credential exposure "
                    "escalated to case qv-3."
                ),
                "ai": {
                    "hypothesis": "Macro loader established persistence ahead of hands-on-keyboard activity",
                    "confidence": "High",
                    "reasoning": [
                        "Office application is not an expected parent for encoded PowerShell.",
                        "Payload dropped to ProgramData and registered under a Microsoft-look-alike task name.",
                        "15-minute interval is consistent with a beacon retry cadence, not a maintenance job.",
                    ],
                    "recommended_actions": [
                        "Delete the OneDriveSyncMaintenance scheduled task",
                        "Quarantine C:\\ProgramData\\odsync.vbs",
                        "Check LSASS access on the host",
                    ],
                },
                "alerts": [
                    {
                        "title": "Office application spawned encoded PowerShell",
                        "attack": "powershell",
                        "product": ProductCategory.EDR,
                        "severity": Severity.HIGH,
                        "confidence": Confidence.HIGH,
                        "impact": Impact.HIGH,
                        "disposition": Disposition.DETECTED,
                        "action": AlertAction.OBSERVED,
                        "status": AlertStatus.RESOLVED,
                        "risk": AlertRiskLevel.HIGH,
                        "rule_id": "EDR-EXE-2201",
                        "rule_name": "Suspicious Office child process - encoded interpreter",
                        "analytic_type": AlertAnalyticType.BEHAVIORAL,
                        "analytic_name": "Endpoint Behavioural Engine",
                        "analytic_desc": "Flags anomalous parent/child process relationships.",
                        "desc": "WINWORD.EXE -> powershell.exe with -enc and hidden window.",
                        "mitigation": "Block Office child-process creation via attack surface reduction rules.",
                        "labels": ["execution", "powershell", "quiet-vault"],
                        "artifacts": ["host_fin_wks", "ip_fin_wks", "user_dliu", "cmd_powershell_enc", "proc_winword"],
                        "offset": m(0),
                        "raw": {
                            "event.dataset": "host",
                            "event.category": "process",
                            "host.name": "FIN-WKS-4471",
                            "user.name": "d.liu",
                            "process.name": "powershell.exe",
                            "process.parent.name": "WINWORD.EXE",
                            "process.command_line": "powershell.exe -nop -w hidden -enc SQBFAFgAIAAoAE4AZQB3AC0ATwBiAGoAZQBjAHQA",
                            "risk_score": 88,
                        },
                    },
                    {
                        "title": "Scheduled task created with Microsoft look-alike name",
                        "attack": "scheduled_task",
                        "product": ProductCategory.EDR,
                        "severity": Severity.HIGH,
                        "confidence": Confidence.HIGH,
                        "impact": Impact.HIGH,
                        "disposition": Disposition.DETECTED,
                        "action": AlertAction.OBSERVED,
                        "status": AlertStatus.RESOLVED,
                        "risk": AlertRiskLevel.HIGH,
                        "rule_id": "EDR-PER-1180",
                        "rule_name": "Scheduled task persistence - user-writable payload path",
                        "analytic_type": AlertAnalyticType.RULE,
                        "analytic_name": "Endpoint Persistence Monitor",
                        "analytic_desc": "Detects task registration pointing at user-writable directories.",
                        "desc": "schtasks created OneDriveSyncMaintenance running wscript against ProgramData.",
                        "mitigation": "Remove the task and restrict script execution from ProgramData.",
                        "labels": ["persistence", "scheduled-task", "quiet-vault"],
                        "artifacts": ["host_fin_wks", "user_dliu", "cmd_schtasks", "file_persist"],
                        "offset": m(2),
                        "raw": {
                            "event.dataset": "host",
                            "event.action": "scheduled_task_created",
                            "host.name": "FIN-WKS-4471",
                            "user.name": "d.liu",
                            "process.command_line": (
                                'schtasks /create /sc minute /mo 15 /tn "OneDriveSyncMaintenance" '
                                '/tr "wscript.exe C:\\ProgramData\\odsync.vbs"'
                            ),
                            "risk_score": 84,
                        },
                    },
                    {
                        "title": "rundll32.exe executed from user-writable path",
                        "attack": "impair_defenses",
                        "product": ProductCategory.EDR,
                        "severity": Severity.MEDIUM,
                        "confidence": Confidence.MEDIUM,
                        "impact": Impact.MEDIUM,
                        "disposition": Disposition.DETECTED,
                        "action": AlertAction.OBSERVED,
                        "status": AlertStatus.RESOLVED,
                        "risk": AlertRiskLevel.MEDIUM,
                        "rule_id": "EDR-DEF-0904",
                        "rule_name": "Defender real-time protection disabled",
                        "analytic_type": AlertAnalyticType.RULE,
                        "analytic_name": "Endpoint Tamper Monitor",
                        "analytic_desc": "Detects modification of endpoint protection settings.",
                        "desc": "Registry write disabled real-time protection shortly after loader execution.",
                        "mitigation": "Enable tamper protection and re-enable real-time scanning.",
                        "labels": ["defense-evasion", "quiet-vault"],
                        "artifacts": ["host_fin_wks", "proc_rundll"],
                        "offset": m(5),
                        "raw": {
                            "event.dataset": "host",
                            "event.action": "registry_value_set",
                            "host.name": "FIN-WKS-4471",
                            "registry.path": "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\DisableAntiSpyware",
                            "registry.data.strings": ["1"],
                            "risk_score": 70,
                        },
                    },
                ],
                "enrichments": [
                    {
                        "target": "case",
                        "name": "Asset ownership and criticality",
                        "type": "CMDB",
                        "provider": "Internal CMDB",
                        "value": "FIN-WKS-4471",
                        "desc": "Finance workstation, Tier-2 asset, primary user d.liu, in scope for SOX controls.",
                        "data": {
                            "hostname": "FIN-WKS-4471",
                            "owner": "d.liu",
                            "department": "Finance",
                            "criticality": "Tier-2",
                            "compliance_scope": ["SOX"],
                            "os": "Windows 11 23H2",
                            "last_patched": "11 days ago",
                        },
                    },
                    {
                        "target": "case",
                        "name": "Containment action",
                        "type": "Remediation",
                        "provider": "CrowdStrike Falcon",
                        "value": "FIN-WKS-4471 network-contained",
                        "desc": "Host placed in network containment; management traffic only.",
                        "data": {"action": "contain", "result": "success", "operator": "alice.chen"},
                    },
                ],
                "comments": [
                    ("alice.chen", "Confirmed the macro chain. Containing FIN-WKS-4471 now. @liam.osullivan heads up, this looks pre-ransomware.", ["liam.osullivan"]),
                    ("liam.osullivan", "Ack. Pulling memory before reimage. Check whether svc_backup was cached on this box.", []),
                    ("alice.chen", "LSASS access confirmed - opening qv-3 for the credential exposure.", []),
                ],
                "playbooks": [
                    {
                        "name": "Investigation",
                        "status": "Success",
                        "user": "alice.chen",
                        "user_input": "Assess the process chain and recommend containment.",
                        "remark": "Verdict: True Positive. Severity raised to High. 3 containment actions recommended.",
                        "started_offset": m(12),
                        "duration": m(2),
                        "messages": [
                            "Serialising case, 3 alerts and 5 artifacts for analysis...",
                            "Retrieved 2 related knowledge records.",
                            "Process ancestry WINWORD.EXE -> powershell.exe -> wscript.exe is inconsistent with business use.",
                            "Scheduled task name mimics a Microsoft service; payload path is user-writable.",
                            "Verdict: True Positive, confidence High.",
                            "Recommended: contain host, delete task, quarantine payload, review LSASS access.",
                        ],
                    },
                ],
            },
            {
                "key": "qv-3-credential-access",
                "title": "LSASS memory read exposing svc_backup credential",
                "category": CaseCategory.EDR,
                "severity": CaseSeverity.CRITICAL,
                "confidence": CaseConfidence.HIGH,
                "impact": CaseImpact.CRITICAL,
                "priority": CasePriority.CRITICAL,
                "status": CaseStatus.RESOLVED,
                "verdict": CaseVerdict.TRUE_POSITIVE,
                "assignee": "liam.osullivan",
                "tags": ["credential-access", "lsass", "quiet-vault"],
                "first_seen": d(6) + h(2) + m(40),
                "ttd": m(3),
                "tta": m(4),
                "ttr": h(9) + m(15),
                "description": (
                    "A non-standard process opened LSASS with read rights. The service account "
                    "svc_backup had a cached session on the host, so its credential must be "
                    "treated as compromised."
                ),
                "summary": (
                    "svc_backup rotated and its interactive logon rights revoked. Reuse of the "
                    "credential on SRV-FILE-02 is tracked in case qv-4."
                ),
                "ai": {
                    "hypothesis": "Credential dumping to enable lateral movement",
                    "confidence": "High",
                    "reasoning": [
                        "PROCESS_VM_READ against LSASS from a process with no legitimate reason to do so.",
                        "svc_backup held a cached session on this host and is a domain-wide backup account.",
                        "Follows persistence in the same session, matching a hands-on-keyboard progression.",
                    ],
                    "recommended_actions": [
                        "Rotate svc_backup immediately",
                        "Revoke interactive logon for service accounts",
                        "Hunt for svc_backup authentication from unexpected sources",
                    ],
                    "blast_radius": "svc_backup is configured on 34 servers",
                },
                "alerts": [
                    {
                        "title": "LSASS process memory read by unsigned binary",
                        "attack": "lsass_memory",
                        "product": ProductCategory.EDR,
                        "severity": Severity.CRITICAL,
                        "confidence": Confidence.HIGH,
                        "impact": Impact.CRITICAL,
                        "disposition": Disposition.DETECTED,
                        "action": AlertAction.OBSERVED,
                        "status": AlertStatus.RESOLVED,
                        "risk": AlertRiskLevel.CRITICAL,
                        "rule_id": "EDR-CRD-0450",
                        "rule_name": "Credential dumping - LSASS handle with VM_READ",
                        "analytic_type": AlertAnalyticType.BEHAVIORAL,
                        "analytic_name": "Endpoint Credential Guard Analytics",
                        "analytic_desc": "Detects suspicious handle requests against LSASS.",
                        "desc": "rundll32.exe requested PROCESS_VM_READ on lsass.exe.",
                        "mitigation": "Enable Credential Guard and restrict service account interactive logon.",
                        "labels": ["credential-access", "lsass", "quiet-vault"],
                        "artifacts": ["host_fin_wks", "user_dliu", "user_svc_backup", "proc_rundll"],
                        "offset": m(0),
                        "raw": {
                            "event.dataset": "host",
                            "event.action": "process_access",
                            "host.name": "FIN-WKS-4471",
                            "process.name": "rundll32.exe",
                            "process.target.name": "lsass.exe",
                            "process.access.mask": "0x1410",
                            "risk_score": 97,
                        },
                    },
                ],
                "enrichments": [
                    {
                        "target": "case",
                        "name": "Service account blast radius",
                        "type": "Identity",
                        "provider": "Microsoft Graph",
                        "value": "svc_backup",
                        "desc": "Backup service account present on 34 servers; interactive logon was permitted.",
                        "data": {
                            "account": "svc_backup",
                            "type": "service",
                            "configured_on_hosts": 34,
                            "interactive_logon_allowed": True,
                            "privileged_groups": ["Backup Operators"],
                            "last_password_rotation": "412 days ago",
                        },
                    },
                    {
                        "target": "case",
                        "name": "Credential rotation",
                        "type": "Remediation",
                        "provider": "CyberArk",
                        "value": "svc_backup rotated",
                        "desc": "Password rotated and interactive logon revoked across all 34 hosts.",
                        "data": {"account": "svc_backup", "rotated": True, "logon_right_revoked": True},
                    },
                ],
                "comments": [
                    ("liam.osullivan", "svc_backup hasn't rotated in 412 days and was on 34 servers. Rotating now, this is the pivot point.", []),
                    ("maya.singh", "Also checking whether svc_backup has any cloud federation. Will report on the cloud side.", []),
                ],
                "playbooks": [
                    {
                        "name": "Investigation",
                        "status": "Success",
                        "user": "liam.osullivan",
                        "user_input": "How far can this credential take the attacker?",
                        "remark": "Verdict: True Positive. Blast radius 34 hosts. Immediate rotation advised.",
                        "started_offset": m(6),
                        "duration": m(2),
                        "messages": [
                            "Serialising case and 1 alert...",
                            "Correlating svc_backup against identity enrichment: 34 hosts, Backup Operators.",
                            "Credential age 412 days exceeds the 90-day policy.",
                            "Verdict: True Positive, confidence High, impact Critical.",
                            "Recommended: rotate immediately, revoke interactive logon, hunt for reuse.",
                        ],
                    },
                    {
                        "name": "CMDB Enrichment",
                        "status": "Success",
                        "user": "automation",
                        "user_input": "",
                        "remark": "Resolved 1 host and 2 identities against the CMDB.",
                        "started_offset": m(3),
                        "duration": m(1),
                        "messages": ["Resolving artifacts against CMDB...", "3 of 4 artifacts matched."],
                    },
                ],
            },
            {
                "key": "qv-4-lateral-movement",
                "title": "svc_backup reused for SMB and RDP access to SRV-FILE-02",
                "category": CaseCategory.NDR,
                "severity": CaseSeverity.CRITICAL,
                "confidence": CaseConfidence.HIGH,
                "impact": CaseImpact.CRITICAL,
                "priority": CasePriority.CRITICAL,
                "status": CaseStatus.IN_PROGRESS,
                "verdict": CaseVerdict.SECURITY_RISK,
                "assignee": "liam.osullivan",
                "tags": ["lateral-movement", "smb", "rdp", "quiet-vault"],
                "first_seen": d(5) + h(21),
                "ttd": m(18),
                "tta": m(11),
                "ttr": None,
                "description": (
                    "The compromised svc_backup credential authenticated from FIN-WKS-4471 to "
                    "SRV-FILE-02 over SMB, followed by an interactive RDP session. A 7-Zip "
                    "archive of finance data was staged on the file server."
                ),
                "summary": "",
                "ai": {
                    "hypothesis": "Hands-on-keyboard lateral movement and data staging before encryption",
                    "confidence": "High",
                    "reasoning": [
                        "svc_backup authenticated interactively, which a service account should never do.",
                        "SMB admin share access immediately preceded an RDP logon from the same source.",
                        "A 7-Zip archive of finance directories was created on the target within 20 minutes.",
                    ],
                    "recommended_actions": [
                        "Isolate SRV-FILE-02",
                        "Preserve the staged archive as evidence",
                        "Block SMB between workstation and server VLANs",
                    ],
                    "open_questions": ["Was the staged archive exfiltrated before containment?"],
                },
                "alerts": [
                    {
                        "title": "Service account interactive SMB admin share access",
                        "attack": "remote_services_smb",
                        "product": ProductCategory.NDR,
                        "severity": Severity.CRITICAL,
                        "confidence": Confidence.HIGH,
                        "impact": Impact.CRITICAL,
                        "disposition": Disposition.DETECTED,
                        "action": AlertAction.OBSERVED,
                        "status": AlertStatus.IN_PROGRESS,
                        "risk": AlertRiskLevel.CRITICAL,
                        "rule_id": "NDR-LAT-0771",
                        "rule_name": "Admin share access by service account",
                        "analytic_type": AlertAnalyticType.BEHAVIORAL,
                        "analytic_name": "East-West Traffic Analytics",
                        "analytic_desc": "Baselines internal authentication and share access patterns.",
                        "desc": "svc_backup accessed ADMIN$ on SRV-FILE-02 from a finance workstation.",
                        "mitigation": "Deny workstation-to-server SMB and restrict admin share access.",
                        "labels": ["lateral-movement", "smb", "quiet-vault"],
                        "artifacts": ["host_fin_wks", "ip_fin_wks", "host_file_srv", "ip_file_srv", "user_svc_backup"],
                        "offset": m(0),
                        "raw": {
                            "event.dataset": "network",
                            "event.action": "smb_share_access",
                            "source.ip": prov.internal_ip(14, 71),
                            "destination.ip": prov.internal_ip(30, 12),
                            "destination.port": 445,
                            "user.name": "svc_backup",
                            "file.directory": "ADMIN$",
                        },
                    },
                    {
                        "title": "Anomalous RDP session to file server",
                        "attack": "remote_services_rdp",
                        "product": ProductCategory.UEBA,
                        "severity": Severity.HIGH,
                        "confidence": Confidence.HIGH,
                        "impact": Impact.HIGH,
                        "disposition": Disposition.DETECTED,
                        "action": AlertAction.OBSERVED,
                        "status": AlertStatus.IN_PROGRESS,
                        "risk": AlertRiskLevel.HIGH,
                        "rule_id": "UEBA-LAT-0233",
                        "rule_name": "First-ever RDP for account and host pair",
                        "analytic_type": AlertAnalyticType.STATISTICAL,
                        "analytic_name": "Behavioural Baseline",
                        "analytic_desc": "Scores authentication events against a 90-day per-identity baseline.",
                        "desc": "svc_backup opened its first RDP session to SRV-FILE-02 in the baseline window.",
                        "mitigation": "Restrict RDP to jump hosts and enforce MFA for administrative access.",
                        "labels": ["lateral-movement", "rdp", "anomaly", "quiet-vault"],
                        "artifacts": ["host_file_srv", "user_svc_backup", "host_fin_wks"],
                        "offset": m(14),
                        "raw": {
                            "event.dataset": "authentication",
                            "event.action": "logon",
                            "winlog.logon.type": 10,
                            "source.ip": prov.internal_ip(14, 71),
                            "host.name": "SRV-FILE-02",
                            "user.name": "svc_backup",
                            "ueba.baseline_deviation": 4.7,
                        },
                    },
                    {
                        "title": "Bulk finance data archived with 7-Zip on SRV-FILE-02",
                        "attack": "archive_collected_data",
                        "product": ProductCategory.EDR,
                        "severity": Severity.HIGH,
                        "confidence": Confidence.HIGH,
                        "impact": Impact.CRITICAL,
                        "disposition": Disposition.DETECTED,
                        "action": AlertAction.OBSERVED,
                        "status": AlertStatus.IN_PROGRESS,
                        "risk": AlertRiskLevel.HIGH,
                        "rule_id": "EDR-COL-1502",
                        "rule_name": "Mass file archive into temp directory",
                        "analytic_type": AlertAnalyticType.BEHAVIORAL,
                        "analytic_name": "Endpoint Behavioural Engine",
                        "analytic_desc": "Detects bulk archive creation consistent with collection staging.",
                        "desc": "4,812 files from the finance share archived to C:\\Windows\\Temp\\nw-fin-q3.7z.",
                        "mitigation": "Preserve the archive, then block egress from the file server.",
                        "labels": ["collection", "staging", "quiet-vault"],
                        "artifacts": ["host_file_srv", "user_svc_backup", "file_staging_archive"],
                        "offset": m(31),
                        "raw": {
                            "event.dataset": "host",
                            "event.action": "file_create",
                            "host.name": "SRV-FILE-02",
                            "user.name": "svc_backup",
                            "file.path": "C:\\Windows\\Temp\\nw-fin-q3.7z",
                            "file.size": 1874233344,
                            "agusta.files_archived": 4812,
                        },
                    },
                ],
                "enrichments": [
                    {
                        "target": "case",
                        "name": "File server criticality",
                        "type": "CMDB",
                        "provider": "Internal CMDB",
                        "value": "SRV-FILE-02",
                        "desc": "Tier-0 file server hosting the finance share; 1,240 users mapped.",
                        "data": {
                            "hostname": "SRV-FILE-02",
                            "criticality": "Tier-0",
                            "role": "Finance file share",
                            "mapped_users": 1240,
                            "backup_status": "last successful 19 hours ago",
                        },
                    },
                    {
                        "target": "case",
                        "name": "Authentication history for svc_backup",
                        "type": "History",
                        "provider": "Elastic",
                        "value": "svc_backup - 90 day baseline",
                        "desc": "No prior interactive logon in 90 days; only scheduled backup service logons.",
                        "data": {
                            "window": "90 days",
                            "interactive_logons_before": 0,
                            "service_logons": 2698,
                            "distinct_sources_before": 2,
                            "distinct_sources_during_incident": 4,
                        },
                    },
                ],
                "comments": [
                    ("liam.osullivan", "Archive is 1.7 GB of finance data staged in Temp. Preserving it before we isolate. @alice.chen we need an exfil check on the egress side.", ["alice.chen"]),
                    ("alice.chen", "DNS beacon case is open as qv-c2, linking it. No large HTTP POST seen yet.", []),
                ],
                "playbooks": [
                    {
                        "name": "Investigation",
                        "status": "Success",
                        "user": "liam.osullivan",
                        "user_input": "Is this staging for exfiltration or encryption?",
                        "remark": "Verdict: Security Risk. Staging consistent with double-extortion preparation.",
                        "started_offset": m(40),
                        "duration": m(3),
                        "messages": [
                            "Serialising case, 3 alerts and 6 artifacts...",
                            "Correlating with cases qv-2 and qv-3 via shared artifact svc_backup.",
                            "Archive creation 31 minutes after first lateral movement indicates automated collection.",
                            "No completed large egress transfer observed; exfiltration likely not finished.",
                            "Verdict: Security Risk. Recommend immediate isolation of SRV-FILE-02.",
                        ],
                    },
                    {
                        "name": "Case Summary",
                        "status": "Running",
                        "user": "liam.osullivan",
                        "user_input": "Draft the exec briefing for the 09:00 stand-up.",
                        "remark": "",
                        "started_offset": m(55),
                        "duration": None,
                        "messages": [
                            "Loading case context...",
                            "Summarising 3 alerts and 2 enrichments...",
                        ],
                    },
                ],
            },
            {
                "key": "qv-5-impact",
                "title": "Shadow copy deletion on srv-db-slave-01 indicating imminent encryption",
                "category": CaseCategory.EDR,
                "severity": CaseSeverity.CRITICAL,
                "confidence": CaseConfidence.HIGH,
                "impact": CaseImpact.CRITICAL,
                "priority": CasePriority.CRITICAL,
                "status": CaseStatus.IN_PROGRESS,
                "verdict": CaseVerdict.SECURITY_RISK,
                "assignee": "liam.osullivan",
                "tags": ["ransomware", "vssadmin", "shadow-copy", "quiet-vault"],
                "first_seen": h(20),
                "ttd": m(2),
                "tta": m(3),
                "ttr": None,
                "description": (
                    "vssadmin.exe deleted all volume shadow copies on a database replica. This is "
                    "the canonical last step before ransomware encryption begins."
                ),
                "summary": "",
                "ai": {
                    "hypothesis": "Ransomware pre-encryption recovery inhibition in progress",
                    "confidence": "High",
                    "reasoning": [
                        "Deleting all shadow copies has no legitimate administrative use on a replica.",
                        "Same intrusion set already staged data on SRV-FILE-02 (case qv-4).",
                        "Ransom note template was written to a public directory 4 minutes later.",
                    ],
                    "recommended_actions": [
                        "Isolate srv-db-slave-01 immediately",
                        "Verify offline backup integrity before any restore",
                        "Declare a major incident and engage the retainer IR firm",
                    ],
                    "time_sensitivity": "Minutes. Encryption typically follows within the hour.",
                },
                "alerts": [
                    {
                        "title": "Shadow Copy Deletion: d.liu ran vssadmin on srv-db-slave-01",
                        "attack": "inhibit_system_recovery",
                        "product": ProductCategory.EDR,
                        "severity": Severity.CRITICAL,
                        "confidence": Confidence.HIGH,
                        "impact": Impact.CRITICAL,
                        "disposition": Disposition.DETECTED,
                        "action": AlertAction.OBSERVED,
                        "status": AlertStatus.NEW,
                        "risk": AlertRiskLevel.CRITICAL,
                        "rule_id": "EDR-01-HOST-Vssadmin-Delete-Shadows",
                        "rule_name": "EDR Vssadmin Delete Shadows",
                        "analytic_type": AlertAnalyticType.RULE,
                        "analytic_name": "EDR Endpoint Security Rule",
                        "analytic_desc": "Detects vssadmin.exe delete shadows command.",
                        "desc": "Command observed: vssadmin.exe delete shadows /all /quiet",
                        "mitigation": "Restrict vssadmin.exe usage and monitor shadow copy deletion.",
                        "labels": ["ransomware", "defense-evasion", "vssadmin"],
                        "artifacts": ["host_db_slave", "user_dliu", "cmd_vssadmin", "proc_vssadmin"],
                        "offset": m(0),
                        "raw": {
                            "@timestamp": "(back-dated by seeder)",
                            "event.dataset": "host",
                            "event.category": "process",
                            "host.name": "srv-db-slave-01",
                            "user.name": "d.liu",
                            "process.name": "vssadmin.exe",
                            "process.command_line": "vssadmin.exe delete shadows /all /quiet",
                            "process.parent.name": "cmd.exe",
                            "risk_score": 100,
                            "message": "Shadow Copy deletion detected - ransomware indicator",
                        },
                    },
                    {
                        "title": "Ransom note template written to public directory",
                        "attack": "data_encrypted_for_impact",
                        "product": ProductCategory.EDR,
                        "severity": Severity.CRITICAL,
                        "confidence": Confidence.HIGH,
                        "impact": Impact.CRITICAL,
                        "disposition": Disposition.DETECTED,
                        "action": AlertAction.OBSERVED,
                        "status": AlertStatus.NEW,
                        "risk": AlertRiskLevel.CRITICAL,
                        "rule_id": "EDR-IMP-0031",
                        "rule_name": "Ransom note filename pattern",
                        "analytic_type": AlertAnalyticType.KEYWORD_MATCH,
                        "analytic_name": "Endpoint Content Inspection",
                        "analytic_desc": "Matches known ransom note filename and content patterns.",
                        "desc": "RESTORE-YOUR-FILES.txt created in C:\\Users\\Public.",
                        "mitigation": "Isolate the host and begin recovery from offline backups.",
                        "labels": ["ransomware", "impact", "quiet-vault"],
                        "artifacts": ["host_db_slave", "file_ransom_note"],
                        "offset": m(4),
                        "raw": {
                            "event.dataset": "host",
                            "event.action": "file_create",
                            "host.name": "srv-db-slave-01",
                            "file.path": "C:\\Users\\Public\\RESTORE-YOUR-FILES.txt",
                            "risk_score": 99,
                        },
                    },
                ],
                "enrichments": [
                    {
                        "target": "case",
                        "name": "Backup recoverability",
                        "type": "Asset",
                        "provider": "Internal CMDB",
                        "value": "srv-db-slave-01",
                        "desc": "Offline backup verified 19 hours old; shadow copies now unavailable.",
                        "data": {
                            "hostname": "srv-db-slave-01",
                            "criticality": "Tier-1",
                            "role": "PostgreSQL read replica",
                            "offline_backup_age_hours": 19,
                            "shadow_copies_present": False,
                            "estimated_data_loss_window_hours": 19,
                        },
                    },
                    {
                        "target": "case",
                        "name": "Campaign correlation",
                        "type": "Correlation",
                        "provider": "AGUSTA",
                        "value": "Operation Quiet Vault - stage 5 of 5",
                        "desc": "Linked to 5 sibling cases through shared artifacts d.liu, svc_backup and FIN-WKS-4471.",
                        "data": {
                            "campaign": "Operation Quiet Vault",
                            "linked_cases": 5,
                            "shared_artifacts": ["d.liu", "svc_backup", "FIN-WKS-4471"],
                            "kill_chain_position": "Impact",
                            "first_observed_days_ago": 6,
                        },
                    },
                ],
                "comments": [
                    ("liam.osullivan", "Shadow copies gone and a ransom note template dropped. Declaring a major incident. Isolating now.", ["alice.chen", "maya.singh"]),
                    ("alice.chen", "Offline backup is 19h old so worst case we lose a day on the replica. Primary is unaffected so far.", []),
                    ("maya.singh", "Cloud side is clean for svc_backup, no federation. Watching CloudTrail.", []),
                ],
                "playbooks": [
                    {
                        "name": "Investigation",
                        "status": "Success",
                        "user": "automation",
                        "user_input": "",
                        "remark": "Verdict: Security Risk. Escalated to Critical. Immediate isolation recommended.",
                        "started_offset": m(2),
                        "duration": m(2),
                        "messages": [
                            "Triggered automatically by module EDR-01-HOST-Vssadmin-Delete-Shadows.",
                            "Serialising case and 2 alerts...",
                            "Matched knowledge record: 'Ransomware pre-encryption indicators'.",
                            "Shadow copy deletion plus ransom note filename is a high-confidence encryption precursor.",
                            "Correlated with 5 open cases sharing artifact svc_backup.",
                            "Verdict: Security Risk, confidence High, priority Critical.",
                        ],
                    },
                    {
                        "name": "Knowledge Extraction",
                        "status": "Pending",
                        "user": "liam.osullivan",
                        "user_input": "Capture the detection and response lessons once contained.",
                        "remark": "",
                        "started_offset": None,
                        "duration": None,
                        "messages": [],
                    },
                ],
                "knowledge": {
                    "title": "Ransomware pre-encryption indicators observed in Operation Quiet Vault",
                    "tags": ["ransomware", "detection", "quiet-vault", "playbook"],
                    "body": (
                        "## Context\n"
                        "Operation Quiet Vault progressed from a macro lure to shadow copy deletion in "
                        "roughly six days across six correlated cases.\n\n"
                        "## Reliable precursors, in observed order\n"
                        "1. Office application spawning an encoded interpreter.\n"
                        "2. Scheduled task registered with a Microsoft look-alike name and a payload in "
                        "a user-writable directory.\n"
                        "3. Endpoint protection tampering via registry policy write.\n"
                        "4. LSASS handle request with PROCESS_VM_READ.\n"
                        "5. Service account performing an interactive logon.\n"
                        "6. Bulk archive creation in a temp directory.\n"
                        "7. `vssadmin delete shadows /all /quiet`.\n\n"
                        "## What worked\n"
                        "Correlating on the shared `svc_backup` artifact grouped six cases that three "
                        "different products had reported separately.\n\n"
                        "## What to change\n"
                        "- Deny interactive logon for all service accounts (svc_backup had it enabled).\n"
                        "- Alert on service account credentials older than 90 days; this one was 412 days old.\n"
                        "- Block workstation-to-server SMB at the VLAN boundary.\n"
                        "- Treat any `vssadmin delete shadows` as an automatic isolation trigger."
                    ),
                },
            },
        ],
        "extra_cases": [
            {
                "key": "qv-c2",
                "title": "DNS tunnelling beacon from FIN-WKS-4471 to cdn-metrics.example",
                "category": CaseCategory.NDR,
                "severity": CaseSeverity.HIGH,
                "confidence": CaseConfidence.MEDIUM,
                "impact": CaseImpact.HIGH,
                "priority": CasePriority.HIGH,
                "status": CaseStatus.ON_HOLD,
                "verdict": CaseVerdict.SUSPICIOUS,
                "assignee": "maya.singh",
                "tags": ["c2", "dns-tunneling", "quiet-vault"],
                "first_seen": d(5) + h(18),
                "ttd": h(1) + m(40),
                "tta": m(35),
                "ttr": None,
                "description": (
                    "High-volume TXT queries with encoded subdomain labels to a newly registered "
                    "domain, on a 15-minute cadence matching the scheduled task from case qv-2."
                ),
                "summary": "Sinkhole requested; awaiting network team change window before blocking.",
                "ai": {
                    "hypothesis": "DNS-based command and control channel",
                    "confidence": "Medium",
                    "reasoning": [
                        "TXT query volume is 340x the host's 30-day baseline.",
                        "Subdomain labels are high-entropy and consistent with base32 encoding.",
                        "Beacon interval matches the 15-minute scheduled task from case qv-2.",
                    ],
                    "recommended_actions": ["Sinkhole the domain", "Block at the DNS resolver", "Confirm payload removal on the host"],
                    "open_questions": ["Volume of data exfiltrated over DNS is not yet quantified"],
                },
                "alerts": [
                    {
                        "title": "Anomalous DNS TXT query volume with encoded labels",
                        "attack": "dns_c2",
                        "product": ProductCategory.NDR,
                        "severity": Severity.HIGH,
                        "confidence": Confidence.MEDIUM,
                        "impact": Impact.HIGH,
                        "disposition": Disposition.ALLOWED,
                        "action": AlertAction.ALLOWED,
                        "status": AlertStatus.IN_PROGRESS,
                        "risk": AlertRiskLevel.HIGH,
                        "rule_id": "NDR-C2-0512",
                        "rule_name": "DNS tunnelling - entropy and volume anomaly",
                        "analytic_type": AlertAnalyticType.STATISTICAL,
                        "analytic_name": "DNS Analytics",
                        "analytic_desc": "Scores query entropy, length and volume against a per-host baseline.",
                        "desc": "1,184 TXT queries in 4 hours to sync.cdn-metrics.example with base32-like labels.",
                        "mitigation": "Sinkhole the domain and restrict outbound DNS to approved resolvers.",
                        "labels": ["c2", "dns", "quiet-vault"],
                        "artifacts": ["host_fin_wks", "ip_fin_wks", "domain_c2_dns", "ip_c2_primary"],
                        "offset": m(0),
                        "raw": {
                            "event.dataset": "network",
                            "event.category": "dns",
                            "source.ip": prov.internal_ip(14, 71),
                            "dns.question.name": "mfrggzdfmztwq2lk.sync.cdn-metrics.example",
                            "dns.question.type": "TXT",
                            "agusta.query_count_4h": 1184,
                            "agusta.baseline_multiplier": 340,
                            "agusta.label_entropy": 3.91,
                        },
                    },
                    {
                        "title": "Threat intelligence match on cdn-metrics.example",
                        "attack": "web_c2",
                        "product": ProductCategory.TI,
                        "severity": Severity.HIGH,
                        "confidence": Confidence.MEDIUM,
                        "impact": Impact.HIGH,
                        "disposition": Disposition.DETECTED,
                        "action": AlertAction.OBSERVED,
                        "status": AlertStatus.IN_PROGRESS,
                        "risk": AlertRiskLevel.HIGH,
                        "rule_id": "TI-IOC-0088",
                        "rule_name": "Domain matched C2 indicator feed",
                        "analytic_type": AlertAnalyticType.EXACT_DATA_MATCH,
                        "analytic_name": "IOC Matching",
                        "analytic_desc": "Matches observed indicators against subscribed threat intelligence.",
                        "desc": "Domain appears in a synthetic demonstration C2 indicator list.",
                        "mitigation": "Block the domain and hunt for other hosts resolving it.",
                        "labels": ["threat-intel", "c2", "quiet-vault"],
                        "artifacts": ["domain_c2_http", "ip_c2_primary"],
                        "offset": h(2),
                        "raw": {
                            "event.dataset": "threatintel",
                            "threat.indicator.type": "domain-name",
                            "threat.indicator.name": "update.cdn-metrics.example",
                            "threat.feed.name": "AGUSTA demonstration indicator set (synthetic)",
                        },
                    },
                ],
                "enrichments": [
                    {
                        "target": "case",
                        "name": "Passive DNS history",
                        "type": "Passive DNS",
                        "provider": "SecurityTrails",
                        "value": "cdn-metrics.example",
                        "desc": "Domain first seen 8 days ago; 3 subdomains, all resolving to one documentation-range address.",
                        "data": {
                            "domain": "cdn-metrics.example",
                            "first_seen_days_ago": 8,
                            "subdomains": ["sync", "update", "cdn"],
                            "resolved_ips": [prov.adversary_ip(47)],
                            "note": "Address is in RFC 5737 TEST-NET-3 and is not a real host.",
                        },
                    },
                ],
                "comments": [
                    ("maya.singh", "Beacon cadence lines up exactly with the 15-min scheduled task in qv-2. Same intrusion. Sinkhole request raised with netops.", []),
                ],
                "playbooks": [
                    {
                        "name": "Threat Intelligence Enrichment",
                        "status": "Failed",
                        "user": "maya.singh",
                        "user_input": "Enrich the C2 domain against all configured providers.",
                        "remark": "Playbook execution failed.",
                        "started_offset": h(3),
                        "duration": m(1),
                        "messages": [
                            "Querying SecurityTrails...",
                            "SecurityTrails returned passive DNS for cdn-metrics.example.",
                            "Querying secondary provider...",
                        ],
                    },
                ],
            },
        ],
        # Extra non-hierarchical links, rendered as "Related" in the case view.
        "related": [
            ("qv-5-impact", "qv-c2"),
            ("qv-4-lateral-movement", "qv-c2"),
        ],
    },
]


# ======================================================================= #
# STORY B - cloud identity compromise. Demonstrates the AWS module,
# cross-domain correlation (IdP -> CloudTrail -> S3) and cloud enrichment.
# ======================================================================= #
STORIES += [
    {
        "key": "driftwood",
        "name": "Cloud identity takeover of m.oyelaran",
        "actor": "Unattributed access broker",
        "narrative": (
            "A sales manager's federated identity is used from an unexpected location "
            "45 minutes after a normal session, MFA is satisfied by a replayed session "
            "cookie, the session attaches AdministratorAccess to a CI user, and then "
            "enumerates and downloads finance reports from S3."
        ),
        "chain": True,
        "stages": [
            {
                "key": "dw-1-impossible-travel",
                "title": "Impossible travel sign-in for m.oyelaran",
                "category": CaseCategory.IAM,
                "severity": CaseSeverity.HIGH,
                "confidence": CaseConfidence.MEDIUM,
                "impact": CaseImpact.HIGH,
                "priority": CasePriority.HIGH,
                "status": CaseStatus.RESOLVED,
                "verdict": CaseVerdict.TRUE_POSITIVE,
                "assignee": "maya.singh",
                "tags": ["identity", "impossible-travel", "session-hijack", "driftwood"],
                "first_seen": d(3) + h(9),
                "ttd": m(6),
                "tta": m(9),
                "ttr": h(2) + m(30),
                "description": (
                    "Two successful sign-ins 45 minutes apart from locations 6,100 km "
                    "apart. The second satisfied MFA without a fresh challenge, "
                    "indicating a replayed session token rather than a password compromise."
                ),
                "summary": (
                    "Session tokens revoked, password reset, MFA re-enrolled. Root cause was "
                    "an adversary-in-the-middle phishing proxy harvesting the session cookie."
                ),
                "ai": {
                    "hypothesis": "Session cookie replay following adversary-in-the-middle phishing",
                    "confidence": "Medium",
                    "reasoning": [
                        "Impossible travel: 6,100 km in 45 minutes.",
                        "Second sign-in reused an existing session token with no MFA challenge.",
                        "Device fingerprint differs from all 90 days of prior sign-ins for this account.",
                    ],
                    "recommended_actions": ["Revoke all sessions", "Reset password", "Re-enrol MFA", "Hunt for AiTM proxy domains"],
                },
                "alerts": [
                    {
                        "title": "Impossible travel between two successful sign-ins",
                        "attack": "valid_accounts_cloud",
                        "product": ProductCategory.IAM,
                        "severity": Severity.HIGH,
                        "confidence": Confidence.MEDIUM,
                        "impact": Impact.HIGH,
                        "disposition": Disposition.ALLOWED,
                        "action": AlertAction.ALLOWED,
                        "status": AlertStatus.RESOLVED,
                        "risk": AlertRiskLevel.HIGH,
                        "rule_id": "OKTA-RSK-0071",
                        "rule_name": "Impossible travel with unfamiliar device",
                        "analytic_type": AlertAnalyticType.STATISTICAL,
                        "analytic_name": "Sign-in Risk Detection",
                        "analytic_desc": "Scores sign-in geo-velocity, device familiarity and token freshness.",
                        "desc": "Successful sign-in from an unfamiliar device 6,100 km from the prior session.",
                        "mitigation": "Revoke sessions and require re-authentication with phishing-resistant MFA.",
                        "labels": ["identity", "impossible-travel", "driftwood"],
                        "artifacts": ["user_moyelaran", "email_moyelaran", "ip_signin_lagos", "ip_signin_vpn"],
                        "offset": m(0),
                        "raw": {
                            "event.dataset": "okta.system",
                            "event.action": "user.session.start",
                            "event.outcome": "success",
                            "user.name": "m.oyelaran",
                            "source.ip": prov.adversary_ip(203),
                            "okta.authentication_context.credential_type": "COOKIE",
                            "okta.security_context.is_proxy": True,
                            "agusta.geo_velocity_km": 6100,
                            "agusta.elapsed_minutes": 45,
                        },
                    },
                ],
                "enrichments": [
                    {
                        "target": "case",
                        "name": "Identity profile and entitlements",
                        "type": "Identity",
                        "provider": "Okta",
                        "value": "m.oyelaran",
                        "desc": "Sales manager; federated to AWS via the NorthwindReadOnly role. MFA was SMS-based.",
                        "data": {
                            "user": "m.oyelaran",
                            "department": "Sales",
                            "federated_roles": ["arn:aws:iam::123456789012:role/NorthwindReadOnly"],
                            "mfa_factors": ["sms"],
                            "phishing_resistant_mfa": False,
                            "prior_countries_90d": 1,
                        },
                    },
                    {
                        "target": "case",
                        "name": "Session revocation",
                        "type": "Remediation",
                        "provider": "Okta",
                        "value": "12 sessions revoked",
                        "desc": "All active sessions revoked and password reset enforced.",
                        "data": {"sessions_revoked": 12, "password_reset": True, "mfa_reenrolled": True},
                    },
                ],
                "comments": [
                    ("maya.singh", "MFA was satisfied by a cookie, not a fresh challenge. That's AiTM, not password spray. Revoking everything.", []),
                    ("alice.chen", "Worth pushing this account group to FIDO2. SMS MFA is the common factor in the last three of these.", ["maya.singh"]),
                ],
                "playbooks": [
                    {
                        "name": "Investigation",
                        "status": "Success",
                        "user": "maya.singh",
                        "user_input": "Password compromise or session theft?",
                        "remark": "Verdict: True Positive. Session replay, not credential compromise.",
                        "started_offset": m(12),
                        "duration": m(2),
                        "messages": [
                            "Serialising case and 1 alert...",
                            "credential_type=COOKIE indicates token reuse rather than password authentication.",
                            "Device fingerprint unseen in 90-day history.",
                            "Verdict: True Positive. Root cause: adversary-in-the-middle session theft.",
                        ],
                    },
                ],
            },
            {
                "key": "dw-2-privilege-escalation",
                "title": "AdministratorAccess attached to IAM user ci-deploy",
                "category": CaseCategory.CLOUD,
                "severity": CaseSeverity.CRITICAL,
                "confidence": CaseConfidence.HIGH,
                "impact": CaseImpact.CRITICAL,
                "priority": CasePriority.CRITICAL,
                "status": CaseStatus.IN_PROGRESS,
                "verdict": CaseVerdict.SECURITY_RISK,
                "assignee": "maya.singh",
                "tags": ["cloud", "privilege-escalation", "iam", "driftwood"],
                "first_seen": d(3) + h(8),
                "ttd": m(3),
                "tta": m(5),
                "ttr": None,
                "description": (
                    "The hijacked session called iam:AttachUserPolicy to grant "
                    "AdministratorAccess to the ci-deploy service user, creating a "
                    "persistent high-privilege backdoor independent of the stolen session."
                ),
                "summary": "",
                "ai": {
                    "hypothesis": "Persistence via IAM privilege escalation on a service identity",
                    "confidence": "High",
                    "reasoning": [
                        "NorthwindReadOnly should not be able to call iam:AttachUserPolicy; a permissions gap was exploited.",
                        "AdministratorAccess on a CI user survives revocation of the human session.",
                        "Action came from the same source address as the impossible travel sign-in.",
                    ],
                    "recommended_actions": [
                        "Detach AdministratorAccess from ci-deploy",
                        "Rotate ci-deploy access keys",
                        "Add an SCP denying iam:Attach* outside the security account",
                    ],
                },
                "alerts": [
                    {
                        "title": "IAM AttachUserPolicy granting AdministratorAccess",
                        "attack": "additional_cloud_roles",
                        "product": ProductCategory.CLOUD,
                        "severity": Severity.CRITICAL,
                        "confidence": Confidence.HIGH,
                        "impact": Impact.CRITICAL,
                        "disposition": Disposition.ALLOWED,
                        "action": AlertAction.ALLOWED,
                        "status": AlertStatus.IN_PROGRESS,
                        "risk": AlertRiskLevel.CRITICAL,
                        # Matches the STREAM_NAME of the bundled AWS Module, so seeded
                        # data and live pipeline output share the same rule identity.
                        "rule_id": "Cloud-01-AWS-IAM-Privilege-Escalation-via-AttachUserPolicy",
                        "rule_name": "AWS IAM Privilege Escalation via AttachUserPolicy",
                        "analytic_type": AlertAnalyticType.RULE,
                        "analytic_name": "CloudTrail Detection Rule",
                        "analytic_desc": "Detects attachment of administrative managed policies to IAM users.",
                        "desc": "AttachUserPolicy attached AdministratorAccess to user ci-deploy.",
                        "mitigation": "Detach the policy, rotate keys, and add a preventative SCP.",
                        "labels": ["cloud", "iam", "privilege-escalation", "driftwood"],
                        "artifacts": ["user_moyelaran", "aws_user_ci", "aws_policy_admin", "aws_role_audit", "ip_signin_vpn", "ua_awscli"],
                        "offset": m(0),
                        "raw": {
                            "eventSource": "iam.amazonaws.com",
                            "eventName": "AttachUserPolicy",
                            "awsRegion": "us-east-1",
                            "sourceIPAddress": prov.adversary_ip(203),
                            "userAgent": "aws-cli/2.15.30 Python/3.11.8 Linux/6.5.0",
                            "userIdentity.type": "AssumedRole",
                            "userIdentity.arn": "arn:aws:iam::123456789012:role/NorthwindReadOnly",
                            "requestParameters.userName": "ci-deploy",
                            "requestParameters.policyArn": "arn:aws:iam::aws:policy/AdministratorAccess",
                            "responseElements": None,
                        },
                    },
                ],
                "enrichments": [
                    {
                        "target": "case",
                        "name": "CI identity usage profile",
                        "type": "Identity",
                        "provider": "AWS IAM",
                        "value": "ci-deploy",
                        "desc": "Deployment identity with two active access keys, one unused for 214 days.",
                        "data": {
                            "user": "ci-deploy",
                            "access_keys": 2,
                            "oldest_key_age_days": 214,
                            "previous_policies": ["arn:aws:iam::123456789012:policy/DeployMinimal"],
                            "now_has_admin": True,
                        },
                    },
                ],
                "comments": [
                    ("maya.singh", "This is the real problem - admin on ci-deploy outlives the session revocation. Detaching and rotating both keys.", ["liam.osullivan"]),
                ],
                "playbooks": [
                    {
                        "name": "Investigation",
                        "status": "Success",
                        "user": "automation",
                        "user_input": "",
                        "remark": "Verdict: Security Risk. Persistent admin backdoor created.",
                        "started_offset": m(3),
                        "duration": m(2),
                        "messages": [
                            "Triggered automatically by module AWS-01-CLOUD-IAM-Privilege-Escalation.",
                            "Correlated with case dw-1 via shared source address.",
                            "AdministratorAccess on a service identity persists beyond session revocation.",
                            "Verdict: Security Risk, priority Critical.",
                        ],
                    },
                ],
            },
            {
                "key": "dw-3-collection",
                "title": "Bulk download of finance reports from S3",
                "category": CaseCategory.CLOUD,
                "severity": CaseSeverity.HIGH,
                "confidence": CaseConfidence.HIGH,
                "impact": CaseImpact.HIGH,
                "priority": CasePriority.HIGH,
                "status": CaseStatus.NEW,
                "verdict": CaseVerdict.UNKNOWN,
                "assignee": None,
                "tags": ["cloud", "collection", "s3", "driftwood"],
                "first_seen": d(3) + h(7),
                "ttd": m(22),
                "tta": None,
                "ttr": None,
                "description": (
                    "After privilege escalation, 612 objects were listed and 88 downloaded "
                    "from the northwind-finance-reports bucket in nine minutes."
                ),
                "summary": "",
                "ai": {
                    "hypothesis": "Data collection from cloud storage ahead of extortion",
                    "confidence": "High",
                    "reasoning": [
                        "ListObjects followed immediately by sequential GetObject is automated collection.",
                        "Bucket holds board-level finance reporting.",
                        "Requests carry the same aws-cli user agent as the privilege escalation.",
                    ],
                    "recommended_actions": ["Enable bucket-level MFA delete", "Review S3 access logs for full object list", "Notify data protection officer"],
                },
                "alerts": [
                    {
                        "title": "Anomalous S3 enumeration and bulk object retrieval",
                        "attack": "data_from_cloud_storage",
                        "product": ProductCategory.CLOUD,
                        "severity": Severity.HIGH,
                        "confidence": Confidence.HIGH,
                        "impact": Impact.HIGH,
                        "disposition": Disposition.ALLOWED,
                        "action": AlertAction.ALLOWED,
                        "status": AlertStatus.NEW,
                        "risk": AlertRiskLevel.HIGH,
                        "rule_id": "AWS-S3-0410",
                        "rule_name": "Bulk object retrieval by unusual principal",
                        "analytic_type": AlertAnalyticType.STATISTICAL,
                        "analytic_name": "CloudTrail Behavioural Analytics",
                        "analytic_desc": "Baselines per-principal S3 access volume.",
                        "desc": "612 objects listed, 88 retrieved in 9 minutes by ci-deploy.",
                        "mitigation": "Restrict the bucket policy and require VPC endpoint access.",
                        "labels": ["cloud", "s3", "collection", "driftwood"],
                        "artifacts": ["aws_user_ci", "aws_bucket_fin", "ip_signin_vpn", "ua_awscli"],
                        "offset": m(0),
                        "raw": {
                            "eventSource": "s3.amazonaws.com",
                            "eventName": "GetObject",
                            "awsRegion": "us-east-1",
                            "sourceIPAddress": prov.adversary_ip(203),
                            "requestParameters.bucketName": "northwind-finance-reports",
                            "agusta.objects_listed": 612,
                            "agusta.objects_retrieved": 88,
                            "agusta.window_minutes": 9,
                        },
                    },
                    {
                        "title": "Cloud infrastructure discovery across three regions",
                        "attack": "cloud_infra_discovery",
                        "product": ProductCategory.CLOUD,
                        "severity": Severity.MEDIUM,
                        "confidence": Confidence.MEDIUM,
                        "impact": Impact.MEDIUM,
                        "disposition": Disposition.ALLOWED,
                        "action": AlertAction.ALLOWED,
                        "status": AlertStatus.NEW,
                        "risk": AlertRiskLevel.MEDIUM,
                        "rule_id": "AWS-DIS-0233",
                        "rule_name": "Describe* API burst from single principal",
                        "analytic_type": AlertAnalyticType.STATISTICAL,
                        "analytic_name": "CloudTrail Behavioural Analytics",
                        "analytic_desc": "Detects reconnaissance bursts of read-only describe calls.",
                        "desc": "47 Describe*/List* calls across us-east-1, eu-west-1 and ap-southeast-1.",
                        "mitigation": "Alert on cross-region describe bursts from non-automation principals.",
                        "labels": ["cloud", "discovery", "driftwood"],
                        "artifacts": ["aws_user_ci", "ip_signin_vpn"],
                        "offset": m(4),
                        "raw": {
                            "eventSource": "ec2.amazonaws.com",
                            "eventName": "DescribeInstances",
                            "sourceIPAddress": prov.adversary_ip(203),
                            "agusta.api_calls": 47,
                            "agusta.regions": ["us-east-1", "eu-west-1", "ap-southeast-1"],
                        },
                    },
                ],
                "enrichments": [
                    {
                        "target": "case",
                        "name": "Bucket data classification",
                        "type": "Asset",
                        "provider": "Internal CMDB",
                        "value": "northwind-finance-reports",
                        "desc": "Confidential financial reporting; in scope for SOX. Versioning on, MFA delete off.",
                        "data": {
                            "bucket": "northwind-finance-reports",
                            "classification": "Confidential",
                            "compliance_scope": ["SOX"],
                            "versioning": True,
                            "mfa_delete": False,
                            "object_count": 612,
                        },
                    },
                ],
                "comments": [],
                "playbooks": [],
            },
        ],
        "extra_cases": [],
        "related": [("dw-3-collection", "qv-4-lateral-movement")],
    },
]


# ======================================================================= #
# STORY C - insider data exfiltration. A fully closed case, demonstrating
# resolution, closure summary and HR handoff.
# ======================================================================= #
STORIES += [
    {
        "key": "greyline",
        "name": "Departing engineer exfiltrating source code",
        "actor": "Insider",
        "narrative": (
            "An engineer under notice archives the pricing engine source tree and uploads "
            "it to a personal file-sharing service. DLP and the web proxy both fire; the "
            "case is confirmed and closed with an HR handoff."
        ),
        "chain": True,
        "stages": [
            {
                "key": "gl-1-dlp",
                "title": "Source code archive matched DLP policy on DEV-WKS-2210",
                "category": CaseCategory.DLP,
                "severity": CaseSeverity.HIGH,
                "confidence": CaseConfidence.HIGH,
                "impact": CaseImpact.HIGH,
                "priority": CasePriority.HIGH,
                "status": CaseStatus.CLOSED,
                "verdict": CaseVerdict.TRUE_POSITIVE,
                "assignee": "alice.chen",
                "tags": ["dlp", "insider", "source-code", "greyline"],
                "first_seen": d(11) + h(6),
                "ttd": m(4),
                "tta": m(15),
                "ttr": d(1) + h(4),
                "description": (
                    "Endpoint DLP matched proprietary source-code fingerprints inside a ZIP "
                    "archive staged on the user's desktop, three days before the user's "
                    "recorded leaving date."
                ),
                "summary": (
                    "Confirmed intentional exfiltration. Upload blocked at the proxy, device "
                    "collected, and the matter handed to HR and Legal. Access revoked on the "
                    "user's final day. No customer data was involved."
                ),
                "ai": {
                    "hypothesis": "Intentional intellectual property theft by a departing employee",
                    "confidence": "High",
                    "reasoning": [
                        "Archive contains 2,214 files fingerprinted as proprietary source.",
                        "Activity occurred 3 days before the recorded leaving date.",
                        "Destination is a personal file-sharing service with no business relationship.",
                    ],
                    "recommended_actions": ["Block the upload", "Preserve the device", "Escalate to HR and Legal"],
                },
                "alerts": [
                    {
                        "title": "Proprietary source code detected in outbound archive",
                        "attack": "archive_collected_data",
                        "product": ProductCategory.DLP,
                        "severity": Severity.HIGH,
                        "confidence": Confidence.HIGH,
                        "impact": Impact.HIGH,
                        "disposition": Disposition.DETECTED,
                        "action": AlertAction.OBSERVED,
                        "status": AlertStatus.RESOLVED,
                        "risk": AlertRiskLevel.HIGH,
                        "rule_id": "DLP-IP-0071",
                        "rule_name": "Source code fingerprint in archive",
                        "analytic_type": AlertAnalyticType.PARTIAL_DATA_MATCH,
                        "analytic_name": "Endpoint DLP",
                        "analytic_desc": "Matches registered document and source fingerprints on endpoints.",
                        "desc": "2,214 fingerprinted source files found in northwind-pricing-engine-src.zip.",
                        "mitigation": "Block egress of matching content and preserve the endpoint.",
                        "labels": ["dlp", "insider", "greyline"],
                        "artifacts": ["user_rkovacs", "host_dev_wks", "file_source_archive"],
                        "offset": m(0),
                        "raw": {
                            "event.dataset": "purview.dlp",
                            "event.action": "policy_match",
                            "host.name": "DEV-WKS-2210",
                            "user.name": "r.kovacs",
                            "file.name": "northwind-pricing-engine-src.zip",
                            "file.size": 48219004,
                            "dlp.policy": "Source Code Protection",
                            "dlp.matched_files": 2214,
                        },
                    },
                ],
                "enrichments": [
                    {
                        "target": "case",
                        "name": "HR employment context",
                        "type": "Identity",
                        "provider": "Internal CMDB",
                        "value": "r.kovacs",
                        "desc": "Senior engineer, notice period ends in 3 days. Repository access to 14 private repos.",
                        "data": {
                            "user": "r.kovacs",
                            "role": "Senior Engineer",
                            "status": "Serving notice",
                            "leaving_in_days": 3,
                            "repository_access": 14,
                        },
                    },
                    {
                        "target": "case",
                        "name": "HR and Legal handoff",
                        "type": "External Ticket",
                        "provider": "Jira",
                        "value": "HR-2291",
                        "desc": "Case handed to HR and Legal; device collected and imaged for preservation.",
                        "data": {"ticket": "HR-2291", "status": "Closed", "device_preserved": True, "access_revoked": True},
                    },
                ],
                "comments": [
                    ("alice.chen", "2,214 fingerprinted files, 3 days before the leaving date. Not accidental. Escalating to HR with the proxy evidence from gl-2.", ["liam.osullivan"]),
                    ("liam.osullivan", "Device imaged and held. HR-2291 raised. Access revoked effective the final day.", []),
                ],
                "playbooks": [
                    {
                        "name": "Investigation",
                        "status": "Success",
                        "user": "alice.chen",
                        "user_input": "Intentional or accidental?",
                        "remark": "Verdict: True Positive. Intentional exfiltration indicated.",
                        "started_offset": m(25),
                        "duration": m(2),
                        "messages": [
                            "Serialising case and 1 alert...",
                            "HR enrichment: user is serving notice, 3 days remaining.",
                            "Archive scope of 2,214 files is inconsistent with accidental staging.",
                            "Verdict: True Positive, confidence High.",
                        ],
                    },
                    {
                        "name": "Knowledge Extraction",
                        "status": "Success",
                        "user": "alice.chen",
                        "user_input": "Record the leaver-monitoring lesson.",
                        "remark": "1 knowledge record created.",
                        "started_offset": h(20),
                        "duration": m(1),
                        "messages": ["Extracting reusable knowledge...", "Created knowledge record."],
                    },
                ],
                "knowledge": {
                    "title": "Leaver risk: raise DLP sensitivity during notice periods",
                    "tags": ["dlp", "insider", "process", "greyline"],
                    "body": (
                        "## Observation\n"
                        "Source-code exfiltration was detected 3 days before a leaving date, but only "
                        "after the archive had already been staged locally.\n\n"
                        "## Recommended control\n"
                        "When HR marks a user as serving notice, automatically:\n"
                        "- move the account into the elevated DLP policy group,\n"
                        "- alert on any archive creation over 10 MB containing registered fingerprints,\n"
                        "- block personal file-sharing categories for that account.\n\n"
                        "## Investigation tip\n"
                        "Always pull the HR employment enrichment early. Notice-period status changed "
                        "this case from 'possible mistake' to 'intentional' in one step."
                    ),
                },
            },
            {
                "key": "gl-2-proxy",
                "title": "Upload of source archive to personal file-sharing service blocked",
                "category": CaseCategory.PROXY,
                "severity": CaseSeverity.MEDIUM,
                "confidence": CaseConfidence.HIGH,
                "impact": CaseImpact.MEDIUM,
                "priority": CasePriority.MEDIUM,
                "status": CaseStatus.CLOSED,
                "verdict": CaseVerdict.TRUE_POSITIVE,
                "assignee": "alice.chen",
                "tags": ["proxy", "insider", "exfiltration", "greyline"],
                "first_seen": d(11) + h(5) + m(30),
                "ttd": m(1),
                "tta": m(18),
                "ttr": d(1) + h(2),
                "description": "Web proxy blocked a 46 MB POST to a personal file-sharing service.",
                "summary": "Upload blocked before completion. Evidence attached to case gl-1.",
                "ai": {
                    "hypothesis": "Exfiltration attempt over web service",
                    "confidence": "High",
                    "reasoning": [
                        "46 MB POST matches the archive size flagged by DLP minutes earlier.",
                        "Destination category is personal file storage, which policy blocks.",
                    ],
                    "recommended_actions": ["Confirm the block held", "Attach as evidence to the DLP case"],
                },
                "alerts": [
                    {
                        "title": "Large POST to personal file storage blocked",
                        "attack": "exfil_cloud_storage",
                        "product": ProductCategory.PROXY,
                        "severity": Severity.MEDIUM,
                        "confidence": Confidence.HIGH,
                        "impact": Impact.MEDIUM,
                        "disposition": Disposition.BLOCKED,
                        "action": AlertAction.DENIED,
                        "status": AlertStatus.RESOLVED,
                        "risk": AlertRiskLevel.MEDIUM,
                        "rule_id": "ZS-DLP-0912",
                        "rule_name": "Blocked upload - personal file storage category",
                        "analytic_type": AlertAnalyticType.RULE,
                        "analytic_name": "Web Inspection",
                        "analytic_desc": "Enforces upload policy by destination category and payload size.",
                        "desc": "46 MB multipart POST to filedrop.example blocked by policy.",
                        "mitigation": "Keep personal file storage blocked for engineering accounts.",
                        "labels": ["proxy", "exfiltration", "blocked", "greyline"],
                        "artifacts": ["user_rkovacs", "host_dev_wks", "url_personal_cloud", "domain_personal_cloud", "file_source_archive"],
                        "offset": m(0),
                        "raw": {
                            "event.dataset": "zscaler.web",
                            "http.request.method": "POST",
                            "http.request.body.bytes": 48219004,
                            "url.domain": "filedrop.example",
                            "user.name": "r.kovacs",
                            "zscaler.action": "blocked",
                            "zscaler.urlcategory": "Personal File Storage",
                        },
                    },
                ],
                "enrichments": [],
                "comments": [],
                "playbooks": [],
            },
        ],
        "extra_cases": [],
        "related": [],
    },
]


# ======================================================================= #
# STORY D - exploitation of an internet-facing application, referencing a
# real CISA KEV vulnerability. Demonstrates vulnerability enrichment and
# WAF -> NDR correlation.
# ======================================================================= #
STORIES += [
    {
        "key": "harborlight",
        "name": "Exploitation of the customer portal via CVE-2023-34362",
        "actor": "Unattributed mass-exploitation actor",
        "narrative": (
            "An internet-facing managed file transfer component behind the customer portal "
            "is probed and then exploited through the MOVEit Transfer SQL injection "
            "(CVE-2023-34362, CISA KEV). A web shell is written and an outbound HTTPS "
            "beacon starts from the DMZ host."
        ),
        "chain": True,
        "stages": [
            {
                "key": "hl-1-exploitation",
                "title": "SQL injection exploitation of customer portal (CVE-2023-34362)",
                "category": CaseCategory.WAF,
                "severity": CaseSeverity.CRITICAL,
                "confidence": CaseConfidence.HIGH,
                "impact": CaseImpact.HIGH,
                "priority": CasePriority.CRITICAL,
                "status": CaseStatus.IN_PROGRESS,
                "verdict": CaseVerdict.TRUE_POSITIVE,
                "assignee": "bob.li",
                "tags": ["waf", "exploitation", "cve-2023-34362", "kev", "harborlight"],
                "first_seen": d(2) + h(11),
                "ttd": m(7),
                "tta": m(13),
                "ttr": None,
                "description": (
                    "After 2,900 blocked probes, three requests matching the MOVEit Transfer "
                    "SQL injection pattern returned HTTP 200, indicating the managed ruleset "
                    "did not cover the exploited path. A web shell was subsequently written."
                ),
                "summary": "",
                "ai": {
                    "hypothesis": "Successful exploitation of a known-exploited vulnerability on an internet-facing host",
                    "confidence": "High",
                    "reasoning": [
                        "Request pattern matches the published CVE-2023-34362 exploitation path.",
                        "Three requests returned 200 after 2,900 were blocked, so the ruleset has a gap.",
                        "A file was written to the uploads directory two minutes later.",
                        "The affected product is on the CISA Known Exploited Vulnerabilities list.",
                    ],
                    "recommended_actions": [
                        "Take the portal out of the load balancer",
                        "Remove the web shell and preserve it for analysis",
                        "Patch or virtual-patch the MOVEit component",
                        "Assume database compromise and rotate portal credentials",
                    ],
                },
                "alerts": [
                    {
                        "title": "SQL injection probes against MOVEit Transfer endpoint",
                        "attack": "exploit_public_app",
                        "product": ProductCategory.WAF,
                        "severity": Severity.HIGH,
                        "confidence": Confidence.HIGH,
                        "impact": Impact.HIGH,
                        "disposition": Disposition.BLOCKED,
                        "action": AlertAction.DENIED,
                        "status": AlertStatus.IN_PROGRESS,
                        "risk": AlertRiskLevel.HIGH,
                        "rule_id": "CF-WAF-100229",
                        "rule_name": "Managed ruleset - SQL injection in query string",
                        "analytic_type": AlertAnalyticType.REGULAR_EXPRESSIONS,
                        "analytic_name": "Managed Ruleset",
                        "analytic_desc": "Signature and pattern matching against HTTP requests.",
                        "desc": "2,900 requests blocked from a single source over 41 minutes.",
                        "mitigation": "Keep the managed ruleset in blocking mode and rate-limit the source.",
                        "labels": ["waf", "sqli", "harborlight"],
                        "artifacts": ["host_portal", "ip_portal", "ip_attacker_scan", "ua_sqlmap", "url_sqli", "cve_moveit", "cwe_sqli"],
                        "offset": m(0),
                        "raw": {
                            "event.dataset": "cloudflare.http",
                            "http.request.method": "POST",
                            "url.path": "/moveitisapi/moveitisapi.dll",
                            "url.query": "action=m2",
                            "source.ip": prov.adversary_ip(119),
                            "user_agent.original": "sqlmap/1.8.2#stable (https://sqlmap.org)",
                            "cloudflare.action": "block",
                            "agusta.blocked_count": 2900,
                            "vulnerability.id": "CVE-2023-34362",
                        },
                    },
                    {
                        "title": "Web shell written to portal uploads directory",
                        "attack": "exploit_public_app",
                        "product": ProductCategory.EDR,
                        "severity": Severity.CRITICAL,
                        "confidence": Confidence.HIGH,
                        "impact": Impact.CRITICAL,
                        "disposition": Disposition.DETECTED,
                        "action": AlertAction.OBSERVED,
                        "status": AlertStatus.IN_PROGRESS,
                        "risk": AlertRiskLevel.CRITICAL,
                        "rule_id": "EDR-WEB-0177",
                        "rule_name": "Executable content written to web-served directory",
                        "analytic_type": AlertAnalyticType.RULE,
                        "analytic_name": "Endpoint File Integrity Monitor",
                        "analytic_desc": "Detects script files written into web-served paths.",
                        "desc": "human2.aspx written to /var/www/portal/uploads by the web service account.",
                        "mitigation": "Remove the file, preserve a copy, and rebuild the host from a known-good image.",
                        "labels": ["webshell", "persistence", "harborlight"],
                        "artifacts": ["host_portal", "ip_portal", "file_webshell"],
                        "offset": m(2),
                        "raw": {
                            "event.dataset": "host",
                            "event.action": "file_create",
                            "host.name": "customer-portal.northwind.example",
                            "file.path": "/var/www/portal/uploads/human2.aspx",
                            "process.name": "MOVEit.DMZ.WebApi",
                            "risk_score": 96,
                        },
                    },
                ],
                "enrichments": [
                    {
                        "target": "case",
                        "name": "Vulnerability intelligence for CVE-2023-34362",
                        "type": "Vulnerability",
                        "provider": "NVD",
                        "value": "CVE-2023-34362",
                        "desc": (
                            "SQL injection in Progress MOVEit Transfer. Listed in the CISA Known "
                            "Exploited Vulnerabilities catalogue."
                        ),
                        "data": {
                            "cve": "CVE-2023-34362",
                            "vendor": prov.KEV_REFERENCES["CVE-2023-34362"]["vendor"],
                            "product": prov.KEV_REFERENCES["CVE-2023-34362"]["product"],
                            "cwe": prov.KEV_REFERENCES["CVE-2023-34362"]["cwe"],
                            "summary": prov.KEV_REFERENCES["CVE-2023-34362"]["summary"],
                            "known_exploited": True,
                            "source": prov.KEV_REFERENCES["CVE-2023-34362"]["source"],
                            "reference": "https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
                        },
                    },
                    {
                        "target": "case",
                        "name": "Internet exposure",
                        "type": "Exposure",
                        "provider": "Internal CMDB",
                        "value": "customer-portal.northwind.example",
                        "desc": "Internet-facing DMZ host, Tier-1, serving 8,400 external customers.",
                        "data": {
                            "hostname": "customer-portal.northwind.example",
                            "zone": "DMZ",
                            "internet_facing": True,
                            "criticality": "Tier-1",
                            "external_users": 8400,
                            "patch_status": "MOVEit component 2 versions behind",
                        },
                    },
                ],
                "comments": [
                    ("bob.li", "2,900 blocked but 3 got a 200 back. Ruleset gap on the ISAPI path. @alice.chen we need the portal out of rotation.", ["alice.chen"]),
                    ("alice.chen", "Pulled from the LB. Web shell preserved. This one is on the KEV list so treat the DB as compromised.", []),
                ],
                "playbooks": [
                    {
                        "name": "Investigation",
                        "status": "Success",
                        "user": "bob.li",
                        "user_input": "Did any of these probes actually succeed?",
                        "remark": "Verdict: True Positive. 3 requests succeeded; assume compromise.",
                        "started_offset": m(20),
                        "duration": m(3),
                        "messages": [
                            "Serialising case, 2 alerts and 7 artifacts...",
                            "Vulnerability enrichment: CVE-2023-34362 is on the CISA KEV list.",
                            "2,900 requests blocked, 3 returned HTTP 200 on the same path.",
                            "File creation in a web-served directory 2 minutes later confirms code execution.",
                            "Verdict: True Positive, confidence High, priority Critical.",
                        ],
                    },
                ],
            },
            {
                "key": "hl-2-c2",
                "title": "Outbound HTTPS beacon from DMZ portal host",
                "category": CaseCategory.NDR,
                "severity": CaseSeverity.HIGH,
                "confidence": CaseConfidence.MEDIUM,
                "impact": CaseImpact.HIGH,
                "priority": CasePriority.HIGH,
                "status": CaseStatus.NEW,
                "verdict": CaseVerdict.SUSPICIOUS,
                "assignee": None,
                "tags": ["c2", "ndr", "dmz", "harborlight"],
                "first_seen": d(2) + h(10),
                "ttd": m(28),
                "tta": None,
                "ttr": None,
                "description": (
                    "Regular 60-second HTTPS connections with near-identical payload sizes "
                    "from the DMZ portal host, beginning after the web shell was written."
                ),
                "summary": "",
                "ai": {
                    "hypothesis": "Web shell operator established an HTTPS command channel",
                    "confidence": "Medium",
                    "reasoning": [
                        "Fixed 60-second interval with low jitter is machine-generated.",
                        "The DMZ host has no business reason to initiate outbound connections.",
                        "Beacon started 6 minutes after the web shell was created in case hl-1.",
                    ],
                    "recommended_actions": ["Block egress from the DMZ", "Capture full packets", "Rebuild the host"],
                },
                "alerts": [
                    {
                        "title": "Periodic HTTPS beacon with uniform payload size",
                        "attack": "web_c2",
                        "product": ProductCategory.NDR,
                        "severity": Severity.HIGH,
                        "confidence": Confidence.MEDIUM,
                        "impact": Impact.HIGH,
                        "disposition": Disposition.ALLOWED,
                        "action": AlertAction.ALLOWED,
                        "status": AlertStatus.NEW,
                        "risk": AlertRiskLevel.HIGH,
                        "rule_id": "NDR-C2-0330",
                        "rule_name": "Low-jitter periodic outbound connection",
                        "analytic_type": AlertAnalyticType.STATISTICAL,
                        "analytic_name": "East-West Traffic Analytics",
                        "analytic_desc": "Detects beaconing by inter-arrival time and payload uniformity.",
                        "desc": "212 connections at 60s intervals, payload variance under 4%.",
                        "mitigation": "Deny outbound initiation from DMZ hosts by default.",
                        "labels": ["c2", "beacon", "harborlight"],
                        "artifacts": ["host_portal", "ip_portal", "ip_c2_primary", "domain_c2_http"],
                        "offset": m(0),
                        "raw": {
                            "event.dataset": "network",
                            "source.ip": prov.dmz_ip(22),
                            "destination.ip": prov.adversary_ip(47),
                            "destination.port": 443,
                            "agusta.connection_count": 212,
                            "agusta.mean_interval_seconds": 60,
                            "agusta.payload_variance_pct": 3.8,
                        },
                    },
                ],
                "enrichments": [],
                "comments": [],
                "playbooks": [],
            },
        ],
        "extra_cases": [],
        "related": [("hl-2-c2", "qv-c2")],
    },
]


# ======================================================================= #
# STORY E - benign and authorised activity. Essential for credibility: a
# real SOC queue is mostly not-a-breach. Demonstrates triage, false
# positive handling and suppression decisions.
# ======================================================================= #
STORIES += [
    {
        "key": "benign",
        "name": "Authorised and benign activity",
        "actor": "Internal, authorised",
        "narrative": (
            "Four cases that look alarming and are not: an authorised red team exercise, "
            "a sysadmin maintenance script, DNS-over-HTTPS to an approved resolver, and "
            "an authorised vulnerability scan."
        ),
        "chain": False,
        "stages": [
            {
                "key": "bn-1-redteam",
                "title": "Credential dumping detected on REDTEAM-KALI-03",
                "category": CaseCategory.EDR,
                "severity": CaseSeverity.CRITICAL,
                "confidence": CaseConfidence.HIGH,
                "impact": CaseImpact.LOW,
                "priority": CasePriority.LOW,
                "status": CaseStatus.CLOSED,
                "verdict": CaseVerdict.FALSE_POSITIVE,
                "assignee": "bob.li",
                "tags": ["red-team", "authorised", "false-positive"],
                "first_seen": d(8) + h(14),
                "ttd": m(2),
                "tta": m(6),
                "ttr": m(24),
                "description": "LSASS access from a known red team host during an authorised exercise window.",
                "summary": (
                    "Authorised red team activity under engagement RT-2026-Q3. Source host and "
                    "account are on the exercise allow-list. Closed as a false positive; a "
                    "suppression rule now covers the exercise window."
                ),
                "ai": {
                    "hypothesis": "Authorised penetration testing activity",
                    "confidence": "High",
                    "reasoning": [
                        "Source host REDTEAM-KALI-03 is registered to engagement RT-2026-Q3.",
                        "Activity falls inside the approved 14:00-18:00 exercise window.",
                        "Account svc_pentest is on the engagement allow-list.",
                    ],
                    "recommended_actions": ["Close as false positive", "Add a scoped suppression for the exercise window"],
                },
                "alerts": [
                    {
                        "title": "LSASS memory read from red team host",
                        "attack": "lsass_memory",
                        "product": ProductCategory.EDR,
                        "severity": Severity.CRITICAL,
                        "confidence": Confidence.HIGH,
                        "impact": Impact.LOW,
                        "disposition": Disposition.EXONERATED,
                        "action": AlertAction.OBSERVED,
                        "status": AlertStatus.SUPPRESSED,
                        "risk": AlertRiskLevel.LOW,
                        "rule_id": "EDR-CRD-0450",
                        "rule_name": "Credential dumping - LSASS handle with VM_READ",
                        "analytic_type": AlertAnalyticType.BEHAVIORAL,
                        "analytic_name": "Endpoint Credential Guard Analytics",
                        "analytic_desc": "Detects suspicious handle requests against LSASS.",
                        "analytic_state": AlertAnalyticState.SUPPRESSED,
                        "desc": "Same detection logic as case qv-3, but from an authorised source.",
                        "mitigation": "No action required. Suppressed for the engagement window.",
                        "labels": ["red-team", "authorised", "false-positive"],
                        "artifacts": ["host_redteam", "user_redteam"],
                        "offset": m(0),
                        "raw": {
                            "event.dataset": "host",
                            "event.action": "process_access",
                            "host.name": "REDTEAM-KALI-03",
                            "user.name": "svc_pentest",
                            "process.target.name": "lsass.exe",
                            "risk_score": 95,
                        },
                    },
                ],
                "enrichments": [
                    {
                        "target": "case",
                        "name": "Red team engagement authorisation",
                        "type": "Observation",
                        "provider": "Jira",
                        "value": "RT-2026-Q3",
                        "desc": "Approved engagement with a defined scope and window; source host is registered.",
                        "data": {
                            "engagement": "RT-2026-Q3",
                            "approved_by": "CISO",
                            "window": "14:00-18:00 local",
                            "allow_listed_hosts": ["REDTEAM-KALI-03"],
                            "allow_listed_accounts": ["svc_pentest"],
                        },
                    },
                ],
                "comments": [
                    ("bob.li", "Checked the engagement register - RT-2026-Q3 covers this host and window. Closing as FP and adding a scoped suppression.", []),
                ],
                "playbooks": [],
            },
            {
                "key": "bn-2-sysadmin",
                "title": "Bulk PowerShell remoting from SRV-JUMP-01",
                "category": CaseCategory.EDR,
                "severity": CaseSeverity.MEDIUM,
                "confidence": CaseConfidence.HIGH,
                "impact": CaseImpact.LOW,
                "priority": CasePriority.LOW,
                "status": CaseStatus.CLOSED,
                "verdict": CaseVerdict.BENIGN,
                "assignee": "bob.li",
                "tags": ["maintenance", "benign", "false-positive"],
                "first_seen": d(7) + h(3),
                "ttd": m(9),
                "tta": m(21),
                "ttr": m(38),
                "description": "PowerShell remoting to 60 servers in 12 minutes from the admin jump host.",
                "summary": (
                    "Scheduled patch pre-check run by a.novak under change CHG-8841. Confirmed with "
                    "the platform team. Closed as benign."
                ),
                "ai": {
                    "hypothesis": "Legitimate administrative maintenance",
                    "confidence": "High",
                    "reasoning": [
                        "Source is the designated admin jump host.",
                        "Targets match the documented patch group for change CHG-8841.",
                        "Script signature matches the approved maintenance script.",
                    ],
                    "recommended_actions": ["Close as benign", "Register the change window to reduce future noise"],
                },
                "alerts": [
                    {
                        "title": "PowerShell remoting to 60 hosts in 12 minutes",
                        "attack": "powershell",
                        "product": ProductCategory.EDR,
                        "severity": Severity.MEDIUM,
                        "confidence": Confidence.HIGH,
                        "impact": Impact.LOW,
                        "disposition": Disposition.EXONERATED,
                        "action": AlertAction.ALLOWED,
                        "status": AlertStatus.RESOLVED,
                        "risk": AlertRiskLevel.LOW,
                        "rule_id": "EDR-EXE-2310",
                        "rule_name": "Fan-out PowerShell remoting",
                        "analytic_type": AlertAnalyticType.STATISTICAL,
                        "analytic_name": "Endpoint Behavioural Engine",
                        "analytic_desc": "Detects one-to-many remote execution patterns.",
                        "desc": "Invoke-Command against 60 hosts from SRV-JUMP-01.",
                        "mitigation": "No action required. Register maintenance windows.",
                        "labels": ["maintenance", "benign"],
                        "artifacts": ["host_jump", "user_sysadmin"],
                        "offset": m(0),
                        "raw": {
                            "event.dataset": "host",
                            "host.name": "SRV-JUMP-01",
                            "user.name": "a.novak",
                            "process.name": "powershell.exe",
                            "agusta.target_host_count": 60,
                            "agusta.change_ticket": "CHG-8841",
                        },
                    },
                ],
                "enrichments": [
                    {
                        "target": "case",
                        "name": "Change management record",
                        "type": "External Ticket",
                        "provider": "ServiceNow",
                        "value": "CHG-8841",
                        "desc": "Approved patch pre-check covering 60 servers in this window.",
                        "data": {"change": "CHG-8841", "status": "Implemented", "approver": "Platform Lead", "hosts_in_scope": 60},
                    },
                ],
                "comments": [
                    ("bob.li", "CHG-8841 matches host count and window exactly. Benign.", []),
                ],
                "playbooks": [],
            },
            {
                "key": "bn-3-doh",
                "title": "Suspected DNS tunnelling to dns.quad9.net",
                "category": CaseCategory.NDR,
                "severity": CaseSeverity.MEDIUM,
                "confidence": CaseConfidence.LOW,
                "impact": CaseImpact.LOW,
                "priority": CasePriority.LOW,
                "status": CaseStatus.CLOSED,
                "verdict": CaseVerdict.FALSE_POSITIVE,
                "assignee": "maya.singh",
                "tags": ["dns", "false-positive", "tuning"],
                "first_seen": d(4) + h(16),
                "ttd": m(52),
                "tta": h(1) + m(10),
                "ttr": m(20),
                "description": "Encrypted DNS traffic to an approved public resolver scored as tunnelling.",
                "summary": (
                    "DNS-over-HTTPS to an approved resolver. The detection scores encrypted DNS "
                    "the same way as tunnelling. Resolver added to the baseline; rule tuned."
                ),
                "ai": {
                    "hypothesis": "Detection tuning issue rather than malicious activity",
                    "confidence": "High",
                    "reasoning": [
                        "Destination is a well-known public DNS resolver on the approved list.",
                        "Traffic pattern is consistent with normal DoH client behaviour.",
                        "No corresponding endpoint or process anomaly on the source host.",
                    ],
                    "recommended_actions": ["Close as false positive", "Add the resolver to the DNS analytics baseline"],
                },
                "alerts": [
                    {
                        "title": "Encrypted DNS traffic scored as tunnelling",
                        "attack": "dns_c2",
                        "product": ProductCategory.NDR,
                        "severity": Severity.MEDIUM,
                        "confidence": Confidence.LOW,
                        "impact": Impact.LOW,
                        "disposition": Disposition.ALLOWED,
                        "action": AlertAction.ALLOWED,
                        "status": AlertStatus.SUPPRESSED,
                        "risk": AlertRiskLevel.LOW,
                        "rule_id": "NDR-C2-0512",
                        "rule_name": "DNS tunnelling - entropy and volume anomaly",
                        "analytic_type": AlertAnalyticType.STATISTICAL,
                        "analytic_name": "DNS Analytics",
                        "analytic_desc": "Scores query entropy, length and volume against a per-host baseline.",
                        "analytic_state": AlertAnalyticState.SUPPRESSED,
                        "desc": "Same rule as case qv-c2, here matching legitimate DoH traffic.",
                        "mitigation": "Baseline approved resolvers to remove this class of false positive.",
                        "labels": ["dns", "false-positive", "tuning"],
                        "artifacts": ["host_jump", "domain_doh"],
                        "offset": m(0),
                        "raw": {
                            "event.dataset": "network",
                            "event.category": "dns",
                            "destination.domain": "dns.quad9.net",
                            "network.protocol": "https",
                            "agusta.label_entropy": 3.6,
                        },
                    },
                ],
                "enrichments": [],
                "comments": [
                    ("maya.singh", "Same rule that caught the real beacon in qv-c2. Tuning the baseline rather than the threshold so we keep the true positives.", []),
                ],
                "playbooks": [],
            },
            {
                "key": "bn-4-scan",
                "title": "WAF blocked injection attempts from internal scanner",
                "category": CaseCategory.WAF,
                "severity": CaseSeverity.LOW,
                "confidence": CaseConfidence.HIGH,
                "impact": CaseImpact.LOW,
                "priority": CasePriority.LOW,
                "status": CaseStatus.CLOSED,
                "verdict": CaseVerdict.BENIGN,
                "assignee": "bob.li",
                "tags": ["waf", "vuln-scan", "benign"],
                "first_seen": d(1) + h(20),
                "ttd": m(15),
                "tta": m(30),
                "ttr": m(12),
                "description": "Authorised weekly vulnerability scan triggered 5,400 WAF blocks.",
                "summary": "Scheduled Qualys scan from SRV-QUALYS-01. Scanner is on the allow-list. Benign.",
                "ai": {
                    "hypothesis": "Authorised vulnerability scanning",
                    "confidence": "High",
                    "reasoning": [
                        "Source is the registered internal scanner appliance.",
                        "Timing matches the weekly scheduled scan window.",
                        "All requests were blocked; no successful responses.",
                    ],
                    "recommended_actions": ["Close as benign", "Exclude the scanner source from WAF alerting"],
                },
                "alerts": [
                    {
                        "title": "High volume of blocked injection attempts from internal source",
                        "attack": "exploit_public_app",
                        "product": ProductCategory.WAF,
                        "severity": Severity.LOW,
                        "confidence": Confidence.HIGH,
                        "impact": Impact.LOW,
                        "disposition": Disposition.BLOCKED,
                        "action": AlertAction.DENIED,
                        "status": AlertStatus.RESOLVED,
                        "risk": AlertRiskLevel.INFO,
                        "rule_id": "CF-WAF-100229",
                        "rule_name": "Managed ruleset - SQL injection in query string",
                        "analytic_type": AlertAnalyticType.REGULAR_EXPRESSIONS,
                        "analytic_name": "Managed Ruleset",
                        "analytic_desc": "Signature and pattern matching against HTTP requests.",
                        "desc": "5,400 requests blocked, all from the internal scanner appliance.",
                        "mitigation": "Add the scanner to the WAF alert exclusion list.",
                        "labels": ["waf", "vuln-scan", "benign"],
                        "artifacts": ["host_portal", "host_scanner", "ip_scanner"],
                        "offset": m(0),
                        "raw": {
                            "event.dataset": "cloudflare.http",
                            "source.ip": prov.internal_ip(9, 40),
                            "cloudflare.action": "block",
                            "agusta.blocked_count": 5400,
                            "agusta.scan_schedule": "weekly-sunday-2000",
                        },
                    },
                ],
                "enrichments": [],
                "comments": [],
                "playbooks": [],
            },
        ],
        "extra_cases": [],
        "related": [],
    },
]


# --------------------------------------------------------------------------- #
# Background queue. Lower-severity, mostly-closed cases so the dashboard,
# severity distribution and MTTD/MTTA/MTTR charts reflect a working SOC rather
# than a handful of showcase incidents. One alert each, deliberately terse.
# --------------------------------------------------------------------------- #

ROUTINE = [
    # (title, category, severity, status, verdict, assignee, days_ago, attack_key, tags)
    ("Blocked drive-by download from newly registered domain", CaseCategory.PROXY, CaseSeverity.LOW, CaseStatus.CLOSED, CaseVerdict.TRUE_POSITIVE, "bob.li", 1, "spearphishing_link", ["proxy", "blocked"]),
    ("Impossible travel for contractor account, confirmed VPN", CaseCategory.IAM, CaseSeverity.MEDIUM, CaseStatus.CLOSED, CaseVerdict.FALSE_POSITIVE, "maya.singh", 2, "valid_accounts_cloud", ["identity", "false-positive"]),
    ("Quarantined credential phishing message", CaseCategory.EMAIL, CaseSeverity.MEDIUM, CaseStatus.CLOSED, CaseVerdict.TRUE_POSITIVE, "bob.li", 2, "spearphishing_link", ["phishing", "quarantined"]),
    ("Unapproved remote access tool installed", CaseCategory.EDR, CaseSeverity.MEDIUM, CaseStatus.RESOLVED, CaseVerdict.TRUE_POSITIVE, "alice.chen", 3, "powershell", ["shadow-it"]),
    ("Public S3 bucket policy detected and reverted", CaseCategory.CLOUD, CaseSeverity.HIGH, CaseStatus.RESOLVED, CaseVerdict.TRUE_POSITIVE, "maya.singh", 4, "data_from_cloud_storage", ["cloud", "misconfiguration"]),
    ("DLP match on personal data in outbound email", CaseCategory.DLP, CaseSeverity.MEDIUM, CaseStatus.RESOLVED, CaseVerdict.TRUE_POSITIVE, "alice.chen", 4, "exfil_cloud_storage", ["dlp", "gdpr"]),
    ("Password spray against VPN portal, all blocked", CaseCategory.IAM, CaseSeverity.MEDIUM, CaseStatus.CLOSED, CaseVerdict.TRUE_POSITIVE, "bob.li", 5, "valid_accounts_cloud", ["identity", "brute-force"]),
    ("Threat intel match on outbound IP, sinkholed", CaseCategory.TI, CaseSeverity.LOW, CaseStatus.CLOSED, CaseVerdict.TRUE_POSITIVE, "maya.singh", 6, "web_c2", ["threat-intel"]),
    ("EICAR test file detected during EDR validation", CaseCategory.EDR, CaseSeverity.INFORMATIONAL, CaseStatus.CLOSED, CaseVerdict.TEST, "liam.osullivan", 6, "impair_defenses", ["test", "validation"]),
    ("Duplicate of phishing campaign case", CaseCategory.EMAIL, CaseSeverity.LOW, CaseStatus.CLOSED, CaseVerdict.DUPLICATE, "bob.li", 7, "spearphishing_attachment", ["phishing", "duplicate"]),
    ("Legacy authentication attempt to deprecated endpoint", CaseCategory.IAM, CaseSeverity.LOW, CaseStatus.CLOSED, CaseVerdict.BENIGN, "maya.singh", 8, "valid_accounts_cloud", ["identity", "legacy"]),
    ("Container image with critical CVE deployed to staging", CaseCategory.CLOUD, CaseSeverity.MEDIUM, CaseStatus.IN_PROGRESS, CaseVerdict.SECURITY_RISK, "maya.singh", 9, "exploit_public_app", ["cloud", "vulnerability"]),
    ("Suspicious OAuth consent grant to third-party app", CaseCategory.IAM, CaseSeverity.HIGH, CaseStatus.ON_HOLD, CaseVerdict.SUSPICIOUS, "alice.chen", 10, "additional_cloud_roles", ["identity", "oauth"]),
    ("Anomalous database read volume from reporting service", CaseCategory.UEBA, CaseSeverity.MEDIUM, CaseStatus.RESOLVED, CaseVerdict.BENIGN, "liam.osullivan", 12, "data_from_cloud_storage", ["ueba", "false-positive"]),
    ("Insufficient telemetry to determine verdict", CaseCategory.SIEM, CaseSeverity.LOW, CaseStatus.CLOSED, CaseVerdict.INSUFFICIENT_DATA, "bob.li", 13, "web_c2", ["telemetry-gap"]),
]
