"""Provenance and safety rules for the AGUSTA demonstration environment.

WHAT IS REAL
------------
The threat *taxonomy* and *vulnerability references* below are real, publicly
published, and redistributable:

* MITRE ATT&CK tactic and technique IDs/names.
  (c) 2015-2026 The MITRE Corporation. ATT&CK is made available under the terms
  at https://attack.mitre.org/resources/legal-and-branding/terms-of-use/ which
  permit redistribution with attribution. Only identifiers and names are used.

* CVE identifiers and their vendor/product/short description, as published in
  the CISA Known Exploited Vulnerabilities (KEV) catalogue at
  https://www.cisa.gov/known-exploited-vulnerabilities-catalog and in NVD.
  KEV is a US Government work in the public domain.

* The EICAR Anti-Malware Test File hashes. EICAR publishes this deliberately
  harmless test string for exactly this purpose (https://www.eicar.org/).
  It is not malware and matching it proves nothing about a real threat.

* Real security vendor and product names (CrowdStrike Falcon, Okta, Proofpoint,
  AWS CloudTrail, ...) used nominatively to describe which product a simulated
  alert would have come from.

WHAT IS SYNTHETIC
-----------------
Everything else. Every organisation, person, hostname, account, IP address,
domain, URL, file path, session ID and timestamp is invented for this
demonstration. The incident narratives are authored scenarios modelled on
publicly documented adversary behaviour; they are NOT real intrusions and must
never be presented as real observed activity, real victims, or real indicators.

NETWORK SAFETY
--------------
All externally-routable-looking addresses come from ranges reserved by the IETF
for documentation, so no real host is ever labelled malicious:

* 192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24  -- RFC 5737 documentation nets
* 2001:db8::/32                                  -- RFC 3849 documentation prefix
* ``.example`` / ``example.com``                  -- RFC 2606 + RFC 6761 reserved

Internal assets use RFC 1918 private space (10.0.0.0/8), which is realistic and
never globally routable.
"""

DATASET_NAME = "AGUSTA Demonstration Environment"

#: Tag applied to every record created by the seeder. Used for idempotency and
#: for the scoped ``--reset`` path, so demo data can be removed without ever
#: touching operator data.
DEMO_TAG = "agusta-demo"

#: Marker embedded in generated identifiers (correlation UIDs, job IDs, ...).
DEMO_PREFIX = "AGUSTA-DEMO"

ATTRIBUTION = (
    "Synthetic demonstration dataset. Incident narratives are authored scenarios, "
    "not real observed activity. MITRE ATT&CK technique identifiers (c) The MITRE "
    "Corporation, used with attribution. CVE references are from the CISA Known "
    "Exploited Vulnerabilities catalogue (public domain). Network indicators use "
    "IETF documentation ranges (RFC 5737 / RFC 2606) and RFC 1918 private space, "
    "so no real host or domain is implicated."
)

# --------------------------------------------------------------------------- #
# Reserved-range building blocks. Use these instead of inventing addresses.
# --------------------------------------------------------------------------- #

#: RFC 2606 reserved TLD - safe for a fictional victim organisation.
ORG_DOMAIN = "northwind.example"
ORG_NAME = "Northwind Trading"

#: RFC 5737 TEST-NET-3 - stands in for adversary infrastructure.
ADVERSARY_NET = "203.0.113"
#: RFC 5737 TEST-NET-2 - stands in for partner / DMZ-facing addresses.
DMZ_NET = "198.51.100"
#: RFC 5737 TEST-NET-1 - stands in for miscellaneous external addresses.
EXTERNAL_NET = "192.0.2"


def adversary_ip(host: int) -> str:
    return f"{ADVERSARY_NET}.{host}"


def dmz_ip(host: int) -> str:
    return f"{DMZ_NET}.{host}"


def external_ip(host: int) -> str:
    return f"{EXTERNAL_NET}.{host}"


def internal_ip(subnet: int, host: int) -> str:
    """RFC 1918 private address for a simulated internal asset."""
    return f"10.20.{subnet}.{host}"


# --------------------------------------------------------------------------- #
# Real MITRE ATT&CK references (identifiers + names only).
# Tactic values must match apps.alerts.models.AlertTactic.
# --------------------------------------------------------------------------- #

ATTACK = {
    "spearphishing_attachment": ("Initial Access", "T1566.001 - Spearphishing Attachment"),
    "spearphishing_link": ("Initial Access", "T1566.002 - Spearphishing Link"),
    "exploit_public_app": ("Initial Access", "T1190 - Exploit Public-Facing Application"),
    "valid_accounts_cloud": ("Initial Access", "T1078.004 - Valid Accounts: Cloud Accounts"),
    "powershell": ("Execution", "T1059.001 - Command and Scripting Interpreter: PowerShell"),
    "scheduled_task": ("Persistence", "T1053.005 - Scheduled Task/Job: Scheduled Task"),
    "additional_cloud_roles": ("Privilege Escalation", "T1098.003 - Account Manipulation: Additional Cloud Roles"),
    "impair_defenses": ("Defense Evasion", "T1562.001 - Impair Defenses: Disable or Modify Tools"),
    "lsass_memory": ("Credential Access", "T1003.001 - OS Credential Dumping: LSASS Memory"),
    "cloud_infra_discovery": ("Discovery", "T1580 - Cloud Infrastructure Discovery"),
    "remote_services_smb": ("Lateral Movement", "T1021.002 - Remote Services: SMB/Windows Admin Shares"),
    "remote_services_rdp": ("Lateral Movement", "T1021.001 - Remote Services: Remote Desktop Protocol"),
    "data_from_cloud_storage": ("Collection", "T1530 - Data from Cloud Storage"),
    "archive_collected_data": ("Collection", "T1560.001 - Archive Collected Data: Archive via Utility"),
    "dns_c2": ("Command and Control", "T1071.004 - Application Layer Protocol: DNS"),
    "web_c2": ("Command and Control", "T1071.001 - Application Layer Protocol: Web Protocols"),
    "exfil_cloud_storage": ("Exfiltration", "T1567.002 - Exfiltration Over Web Service: Cloud Storage"),
    "inhibit_system_recovery": ("Impact", "T1490 - Inhibit System Recovery"),
    "data_encrypted_for_impact": ("Impact", "T1486 - Data Encrypted for Impact"),
}


def tactic_of(key: str) -> str:
    return ATTACK[key][0]


def technique_of(key: str) -> str:
    return ATTACK[key][1]


# --------------------------------------------------------------------------- #
# Real CVEs from the CISA Known Exploited Vulnerabilities catalogue.
# Public domain; descriptions condensed from the published catalogue entries.
# --------------------------------------------------------------------------- #

KEV_REFERENCES = {
    "CVE-2023-34362": {
        "vendor": "Progress Software",
        "product": "MOVEit Transfer",
        "summary": (
            "SQL injection in Progress MOVEit Transfer allows an unauthenticated attacker "
            "to access the database and execute privileged commands."
        ),
        "cwe": "CWE-89",
        "source": "CISA Known Exploited Vulnerabilities catalogue",
    },
    "CVE-2021-44228": {
        "vendor": "Apache Software Foundation",
        "product": "Apache Log4j2",
        "summary": (
            "JNDI lookups in Log4j2 allow a remote attacker who controls log messages to "
            "execute arbitrary code (Log4Shell)."
        ),
        "cwe": "CWE-917",
        "source": "CISA Known Exploited Vulnerabilities catalogue",
    },
    "CVE-2017-0144": {
        "vendor": "Microsoft",
        "product": "Windows SMBv1",
        "summary": (
            "Remote code execution in Microsoft SMBv1 via crafted packets (EternalBlue)."
        ),
        "cwe": "CWE-94",
        "source": "CISA Known Exploited Vulnerabilities catalogue",
    },
}

# --------------------------------------------------------------------------- #
# EICAR Anti-Malware Test File. Published by EICAR as a deliberately harmless
# detection test artefact. Safe to reference; not malware.
# --------------------------------------------------------------------------- #

EICAR_MD5 = "44d88612fea8a8f36de82e1278abb02f"
EICAR_SHA256 = "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f"
EICAR_NOTE = (
    "Hash matches the EICAR Anti-Malware Test File, a harmless published test "
    "artefact. Used here so the demonstration contains no real malware sample."
)
