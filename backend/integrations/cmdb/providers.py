import hashlib
import ipaddress
import re

from apps.artifacts.models import ArtifactType
from integrations.cmdb.models import CMDBProviderResult

MOCK_CMDB_PROVIDER_NAME = "MockCMDBProvider"

SUPPORTED_ARTIFACT_TYPES = {
    ArtifactType.HOSTNAME,
    ArtifactType.IP_ADDRESS,
    ArtifactType.MAC_ADDRESS,
    ArtifactType.USER_NAME,
    ArtifactType.USER,
    ArtifactType.ACCOUNT,
    ArtifactType.EMAIL_ADDRESS,
    ArtifactType.EMAIL,
    ArtifactType.ENDPOINT,
    ArtifactType.DEVICE,
    ArtifactType.RESOURCE_UID,
    ArtifactType.RESOURCE,
    ArtifactType.PORT,
    ArtifactType.SUBNET,
    ArtifactType.SERIAL_NUMBER,
}

BUSINESS_PROFILES = [
    {
        "bucket": "ecommerce-prod",
        "service_id": "SVC-ECOM-001",
        "service_name": "E-Commerce Platform",
        "business_criticality": "Critical",
        "owner_team": "WebOps Team",
        "department": "Online Business",
        "environment": "Production",
        "network_zone": "DMZ",
    },
    {
        "bucket": "database-prod",
        "service_id": "SVC-DATA-002",
        "service_name": "Core Database Service",
        "business_criticality": "Critical",
        "owner_team": "DBA Team",
        "department": "IT Operations",
        "environment": "Production",
        "network_zone": "Internal Prod",
    },
    {
        "bucket": "employee-office",
        "service_id": "SVC-ENDUSER-003",
        "service_name": "Employee Endpoint Service",
        "business_criticality": "Medium",
        "owner_team": "Endpoint Team",
        "department": "Corporate IT",
        "environment": "Office",
        "network_zone": "Office LAN",
    },
    {
        "bucket": "identity-security",
        "service_id": "SVC-IAM-004",
        "service_name": "Identity and Access Management",
        "business_criticality": "High",
        "owner_team": "IAM Team",
        "department": "Security",
        "environment": "Production",
        "network_zone": "Internal Prod",
    },
    {
        "bucket": "cloud-workload",
        "service_id": "SVC-CLOUD-005",
        "service_name": "Cloud Workload Platform",
        "business_criticality": "High",
        "owner_team": "CloudOps Team",
        "department": "Cloud Platform",
        "environment": "Cloud",
        "network_zone": "Cloud VPC",
    },
    {
        "bucket": "network-infra",
        "service_id": "SVC-NET-006",
        "service_name": "Enterprise Network Infrastructure",
        "business_criticality": "High",
        "owner_team": "Network Team",
        "department": "Infrastructure",
        "environment": "Production",
        "network_zone": "Management",
    },
]

PROFILE_BY_BUCKET = {profile["bucket"]: profile for profile in BUSINESS_PROFILES}
USER_PREFIX_PROFILES = {
    "adm": "identity-security",
    "admin": "identity-security",
    "sec": "identity-security",
    "soc": "identity-security",
    "dba": "database-prod",
    "db": "database-prod",
    "hr": "employee-office",
    "user": "employee-office",
    "emp": "employee-office",
    "cloud": "cloud-workload",
    "aws": "cloud-workload",
    "dev": "cloud-workload",
}
HOST_PREFIX_PROFILES = {
    "prod-web": "ecommerce-prod",
    "web": "ecommerce-prod",
    "api": "ecommerce-prod",
    "db": "database-prod",
    "mysql": "database-prod",
    "postgres": "database-prod",
    "pc": "employee-office",
    "lap": "employee-office",
    "iam": "identity-security",
    "ad": "identity-security",
    "ec2": "cloud-workload",
    "aws": "cloud-workload",
    "fw": "network-infra",
    "rtr": "network-infra",
    "sw": "network-infra",
    "vpn": "network-infra",
}
IP_NETWORK_PROFILES = [
    (ipaddress.ip_network("192.168.10.0/24"), "ecommerce-prod"),
    (ipaddress.ip_network("172.16.0.0/20"), "database-prod"),
    (ipaddress.ip_network("10.0.0.0/16"), "employee-office"),
    (ipaddress.ip_network("10.10.0.0/16"), "ecommerce-prod"),
    (ipaddress.ip_network("10.20.0.0/16"), "database-prod"),
    (ipaddress.ip_network("10.30.0.0/16"), "identity-security"),
    (ipaddress.ip_network("10.40.0.0/16"), "cloud-workload"),
    (ipaddress.ip_network("172.31.0.0/24"), "network-infra"),
    (ipaddress.ip_network("172.31.0.0/16"), "cloud-workload"),
    (ipaddress.ip_network("203.0.113.0/24"), "network-infra"),
]


class BaseCMDBProvider:
    name = ""

    def lookup(self, artifact_type, artifact_value):
        raise NotImplementedError


class MockCMDBProvider(BaseCMDBProvider):
    name = MOCK_CMDB_PROVIDER_NAME

    def lookup(self, artifact_type, artifact_value):
        artifact_type = _artifact_type_value(artifact_type)
        value = str(artifact_value or "").strip()
        if not value:
            return _unsupported(artifact_type=artifact_type, artifact_value=value, error="artifact_value is empty.")
        if artifact_type not in SUPPORTED_ARTIFACT_TYPES:
            return _unsupported(
                artifact_type=artifact_type,
                artifact_value=value,
                error=f"Unsupported artifact type for CMDB lookup: {artifact_type}",
            )

        if artifact_type in {ArtifactType.USER_NAME, ArtifactType.USER, ArtifactType.ACCOUNT}:
            return self._identity_context(artifact_type, value)
        if artifact_type in {ArtifactType.EMAIL_ADDRESS, ArtifactType.EMAIL}:
            return self._email_context(artifact_type, value)
        if artifact_type == ArtifactType.PORT:
            return self._port_context(artifact_type, value)
        if artifact_type == ArtifactType.SUBNET:
            return self._subnet_context(artifact_type, value)
        if artifact_type in {ArtifactType.RESOURCE_UID, ArtifactType.RESOURCE}:
            return self._resource_context(artifact_type, value)
        if artifact_type in {ArtifactType.HOSTNAME, ArtifactType.ENDPOINT, ArtifactType.DEVICE}:
            return self._asset_context(artifact_type, value, self._profile_for_hostname(value), hostname=value)
        if artifact_type == ArtifactType.IP_ADDRESS:
            try:
                ipaddress.ip_address(value)
            except ValueError:
                return _unsupported(artifact_type=artifact_type, artifact_value=value, error="Invalid IP address.")
            return self._asset_context(artifact_type, value, self._profile_for_ip(value), ip_address=value)
        if artifact_type == ArtifactType.MAC_ADDRESS:
            return self._asset_context(artifact_type, value, self._profile_for_mac(value), mac_address=value)
        if artifact_type == ArtifactType.SERIAL_NUMBER:
            return self._asset_context(artifact_type, value, self._profile_for_serial(value), serial_number=value)

        return _unsupported(artifact_type=artifact_type, artifact_value=value, error="Unsupported CMDB lookup.")

    def _asset_context(
        self,
        artifact_type,
        value,
        profile,
        *,
        hostname=None,
        ip_address=None,
        mac_address=None,
        serial_number=None,
    ):
        seed = self._seed(artifact_type, value)
        asset_type = self._asset_type_for_profile(profile, value)
        hostname = hostname or self._hostname(seed, asset_type)
        ip_address = ip_address or self._ip(seed, profile)
        mac_address = mac_address or self._mac(seed)
        serial_number = serial_number or f"SN-{self._token(seed, 10)}"
        return CMDBProviderResult(
            artifact_type=artifact_type,
            artifact_value=value,
            provider=self.name,
            supported=True,
            record_type="asset",
            asset={
                "asset_id": f"AST-{self._token(profile['bucket'] + ':' + value, 8)}",
                "asset_type": asset_type,
                "hostname": hostname,
                "ip_addresses": [ip_address],
                "mac_address": mac_address,
                "serial_number": serial_number,
                "status": self._pick(seed + ":status", ["Active", "Active", "Active", "Maintenance"]),
                "environment": profile["environment"],
                "network_zone": profile["network_zone"],
                "location": self._pick(seed + ":location", ["Shanghai DC", "Beijing DC", "Cloud", "Office", "Remote"]),
            },
            business=self._business(profile),
            owner=self._owner(profile, seed),
            related={
                "primary_user": self._owner(profile, seed)["user_id"],
                "nearby_assets": self._nearby_assets(seed, profile, asset_type),
                "service_assets_hint": f"Assets in {profile['service_id']} usually share owner_team={profile['owner_team']} and zone={profile['network_zone']}.",
            },
            raw={"source": self.name, "rule": "asset-context"},
        )

    def _identity_context(self, artifact_type, value):
        profile = self._profile_for_user(value)
        seed = self._seed(artifact_type, value)
        workstation = self._asset_context(ArtifactType.HOSTNAME, f"pc-{self._safe_name(value)}", profile)
        return CMDBProviderResult(
            artifact_type=artifact_type,
            artifact_value=value,
            provider=self.name,
            supported=True,
            record_type="identity",
            identity={
                "user_id": value,
                "display_name": self._display_name(value),
                "department": profile["department"],
                "job_title": self._pick(seed + ":title", ["Engineer", "Analyst", "Administrator", "Manager"]),
                "employment_status": "Active",
                "privilege_level": self._pick(seed + ":priv", ["Standard", "Standard", "Privileged", "High/Critical"]),
            },
            business=self._business(profile),
            owner=self._owner(profile, seed),
            related={
                "primary_endpoint": workstation.asset,
                "accounts": [value, f"{value}@corp.example"],
                "common_services": [profile["service_id"]],
            },
            raw={"source": self.name, "rule": "identity-context"},
        )

    def _email_context(self, artifact_type, value):
        local_part = value.split("@", 1)[0] if "@" in value else value
        domain = value.split("@", 1)[1] if "@" in value else "corp.example"
        identity = self._identity_context(ArtifactType.USER_NAME, local_part)
        return CMDBProviderResult(
            artifact_type=artifact_type,
            artifact_value=value,
            provider=self.name,
            supported=True,
            record_type="email_identity",
            mailbox={
                "email_address": value,
                "mail_domain": domain,
                "mail_platform": self._pick(domain, ["Microsoft 365", "Google Workspace", "Exchange Online"]),
                "mailbox_status": "Active",
            },
            identity=identity.identity,
            business=identity.business,
            owner=identity.owner,
            related=identity.related,
            raw={"source": self.name, "rule": "email-context"},
        )

    def _port_context(self, artifact_type, value):
        if not value.isdigit() or not 1 <= int(value) <= 65535:
            return _unsupported(artifact_type=artifact_type, artifact_value=value, error="Invalid TCP/UDP port.")
        port = int(value)
        profile = self._profile_for_port(port)
        seed = self._seed(artifact_type, value)
        return CMDBProviderResult(
            artifact_type=artifact_type,
            artifact_value=value,
            provider=self.name,
            supported=True,
            record_type="network_exposure",
            port={
                "port": port,
                "protocol": self._pick(seed + ":proto", ["TCP", "TCP", "UDP"]),
                "common_service": self._service_name_for_port(port),
                "exposure_level": self._pick(seed + ":exposure", ["Internal", "Internet-facing", "Management-only"]),
            },
            business=self._business(profile),
            related={
                "related_assets": self._nearby_assets(seed, profile, self._asset_type_for_profile(profile, value)),
            },
            raw={"source": self.name, "rule": "port-context"},
        )

    def _subnet_context(self, artifact_type, value):
        try:
            network = ipaddress.ip_network(value, strict=False)
        except ValueError:
            return _unsupported(artifact_type=artifact_type, artifact_value=value, error="Invalid subnet.")
        profile = self._profile_for_ip(str(network.network_address))
        seed = self._seed(artifact_type, value)
        return CMDBProviderResult(
            artifact_type=artifact_type,
            artifact_value=value,
            provider=self.name,
            supported=True,
            record_type="subnet",
            subnet={
                "cidr": str(network),
                "network_zone": profile["network_zone"],
                "environment": profile["environment"],
                "estimated_asset_count": self._stable_int(seed + ":count") % 80 + 10,
                "owner_team": profile["owner_team"],
            },
            business=self._business(profile),
            related={
                "related_assets": self._nearby_assets(seed, profile, self._asset_type_for_profile(profile, value), count=5),
            },
            raw={"source": self.name, "rule": "subnet-context"},
        )

    def _resource_context(self, artifact_type, value):
        profile = self._profile_for_resource(value)
        seed = self._seed(artifact_type, value)
        return CMDBProviderResult(
            artifact_type=artifact_type,
            artifact_value=value,
            provider=self.name,
            supported=True,
            record_type="resource",
            resource={
                "resource_id": value,
                "resource_type": self._resource_type(value),
                "provider": self._resource_provider(value),
                "region": self._pick(seed + ":region", ["cn-shanghai", "cn-beijing", "us-east-1", "ap-southeast-1"]),
                "status": self._pick(seed + ":status", ["Running", "Available", "Active", "Stopped"]),
            },
            business=self._business(profile),
            owner=self._owner(profile, seed),
            related={"related_assets": self._nearby_assets(seed, profile, "CloudInstance")},
            raw={"source": self.name, "rule": "resource-context"},
        )

    def _profile_for_ip(self, value):
        ip = ipaddress.ip_address(value)
        for network, bucket in IP_NETWORK_PROFILES:
            if ip in network:
                return PROFILE_BY_BUCKET[bucket]
        if ip.is_private:
            return PROFILE_BY_BUCKET[self._pick(str(ip), ["employee-office", "database-prod", "cloud-workload"])]
        return PROFILE_BY_BUCKET[self._pick(str(ip), ["ecommerce-prod", "network-infra", "cloud-workload"])]

    def _profile_for_hostname(self, value):
        normalized = value.lower()
        for prefix, bucket in HOST_PREFIX_PROFILES.items():
            if normalized.startswith(prefix) or f"-{prefix}" in normalized:
                return PROFILE_BY_BUCKET[bucket]
        return self._profile_by_hash(value)

    def _profile_for_user(self, value):
        normalized = value.lower().split("@", 1)[0]
        for prefix, bucket in USER_PREFIX_PROFILES.items():
            if normalized.startswith(prefix):
                return PROFILE_BY_BUCKET[bucket]
        return PROFILE_BY_BUCKET[self._pick(normalized, ["employee-office", "identity-security", "database-prod", "cloud-workload"])]

    def _profile_for_mac(self, value):
        vendor_hint = value.upper().replace("-", ":")[:8]
        if vendor_hint in {"00:1A:2B", "3C:52:82", "B8:27:EB"}:
            return PROFILE_BY_BUCKET["employee-office"]
        return self._profile_by_hash(value)

    def _profile_for_serial(self, value):
        lower = value.lower()
        if lower.startswith(("fw", "rtr", "sw", "net")):
            return PROFILE_BY_BUCKET["network-infra"]
        if lower.startswith(("ec2", "aws", "gce", "az")):
            return PROFILE_BY_BUCKET["cloud-workload"]
        return self._profile_by_hash(value)

    def _profile_for_port(self, port):
        if port in {80, 443, 8080, 8443}:
            return PROFILE_BY_BUCKET["ecommerce-prod"]
        if port in {1433, 1521, 3306, 5432, 6379, 9200}:
            return PROFILE_BY_BUCKET["database-prod"]
        if port in {22, 23, 161, 3389, 5900}:
            return PROFILE_BY_BUCKET["network-infra"]
        return self._profile_by_hash(str(port))

    def _profile_for_resource(self, value):
        lower = value.lower()
        if lower.startswith(("arn:", "i-", "ec2", "aws", "gcp", "gce", "az", "/subscriptions/")):
            return PROFILE_BY_BUCKET["cloud-workload"]
        if any(word in lower for word in ["policy", "role", "user", "iam"]):
            return PROFILE_BY_BUCKET["identity-security"]
        return self._profile_by_hash(value)

    def _profile_by_hash(self, seed):
        return self._pick(seed, BUSINESS_PROFILES)

    def _asset_type_for_profile(self, profile, value):
        lower = value.lower()
        if profile["bucket"] == "network-infra":
            return self._pick(value, ["Firewall", "Router", "Switch", "VPN Gateway", "Load Balancer"])
        if profile["bucket"] == "cloud-workload":
            return "CloudInstance"
        if profile["bucket"] == "database-prod" or any(word in lower for word in ["db", "sql", "mysql", "postgres"]):
            return "Database"
        if profile["bucket"] == "employee-office" or lower.startswith(("pc", "lap", "desktop")):
            return "Workstation"
        return "Server"

    def _business(self, profile):
        return {
            "service_id": profile["service_id"],
            "service_name": profile["service_name"],
            "business_criticality": profile["business_criticality"],
            "department": profile["department"],
            "environment": profile["environment"],
        }

    def _owner(self, profile, seed):
        user_prefix = {
            "WebOps Team": "webops",
            "DBA Team": "dba",
            "Endpoint Team": "endpoint",
            "IAM Team": "iam",
            "CloudOps Team": "cloudops",
            "Network Team": "netops",
        }.get(profile["owner_team"], "owner")
        return {
            "owner_team": profile["owner_team"],
            "user_id": f"{user_prefix}_{self._token(seed + ':owner', 4).lower()}",
            "oncall": f"{profile['owner_team'].lower().replace(' ', '-')}-oncall",
        }

    def _nearby_assets(self, seed, profile, asset_type, count=3):
        return [
            {
                "asset_id": f"AST-{self._token(seed + ':nearby:' + str(index), 8)}",
                "asset_type": asset_type,
                "hostname": self._hostname(seed + f":nearby:{index}", asset_type),
                "ip_address": self._ip(seed + f":nearby:{index}", profile),
                "relationship": self._pick(
                    seed + f":rel:{index}",
                    ["same_service", "same_subnet", "same_owner_team", "same_application_tier"],
                ),
            }
            for index in range(1, count + 1)
        ]

    def _hostname(self, seed, asset_type):
        prefix = {
            "Server": "srv",
            "Database": "db",
            "Workstation": "pc",
            "CloudInstance": "ec2",
            "Firewall": "fw",
            "Router": "rtr",
            "Switch": "sw",
            "VPN Gateway": "vpn",
            "Load Balancer": "lb",
        }.get(asset_type, "asset")
        return f"{prefix}-{self._token(seed + ':host', 6).lower()}"

    def _ip(self, seed, profile):
        bucket_octet = {
            "ecommerce-prod": 10,
            "database-prod": 20,
            "employee-office": 0,
            "identity-security": 30,
            "cloud-workload": 40,
            "network-infra": 31,
        }.get(profile["bucket"], 50)
        stable = self._stable_int(seed)
        return f"10.{bucket_octet}.{stable % 250}.{stable // 250 % 250}"

    def _mac(self, seed):
        token = self._token(seed + ":mac", 12)
        return ":".join(token[index:index + 2] for index in range(0, 12, 2))

    def _resource_provider(self, value):
        lower = value.lower()
        if lower.startswith(("arn:", "aws", "i-")):
            return "AWS"
        if lower.startswith(("gcp", "gce")):
            return "GCP"
        if lower.startswith(("az", "/subscriptions/")):
            return "Azure"
        return "Internal"

    def _resource_type(self, value):
        lower = value.lower()
        if "s3" in lower or "bucket" in lower:
            return "StorageBucket"
        if "db" in lower or "rds" in lower:
            return "Database"
        if "role" in lower or "policy" in lower or "iam" in lower:
            return "IdentityResource"
        return "CloudResource"

    def _service_name_for_port(self, port):
        return {
            22: "SSH",
            25: "SMTP",
            53: "DNS",
            80: "HTTP",
            443: "HTTPS",
            1433: "MSSQL",
            1521: "Oracle",
            3306: "MySQL",
            5432: "PostgreSQL",
            6379: "Redis",
            9200: "Elasticsearch",
        }.get(port, "Unknown")

    @staticmethod
    def _safe_name(value):
        return re.sub(r"[^a-zA-Z0-9-]+", "-", value).strip("-").lower() or "unknown"

    @staticmethod
    def _display_name(value):
        name = re.sub(r"[^a-zA-Z0-9]+", " ", value).strip()
        return name.title() if name else value

    @staticmethod
    def _seed(artifact_type, value):
        return f"{artifact_type}:{value}"

    @staticmethod
    def _stable_int(seed):
        return int(hashlib.sha256(str(seed).encode("utf-8")).hexdigest()[:12], 16)

    def _token(self, seed, length):
        return hashlib.sha256(str(seed).encode("utf-8")).hexdigest()[:length].upper()

    def _pick(self, seed, options):
        return options[self._stable_int(seed) % len(options)]


def _artifact_type_value(artifact_type):
    return artifact_type.value if hasattr(artifact_type, "value") else str(artifact_type)


def _unsupported(*, artifact_type, artifact_value, error):
    return CMDBProviderResult(
        artifact_type=artifact_type,
        artifact_value=artifact_value,
        provider=MOCK_CMDB_PROVIDER_NAME,
        supported=False,
        error=error,
        raw={"source": MOCK_CMDB_PROVIDER_NAME, "error": error},
    )


def get_providers():
    return {MOCK_CMDB_PROVIDER_NAME: MockCMDBProvider()}
