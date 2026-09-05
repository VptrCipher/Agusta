import random
import uuid
from datetime import datetime

from mock.siem import settings


class BruteForceScenario(object):
    def __init__(self, target_user=None):
        self.target_user = target_user or random.choice(settings.USERS)
        self.target_host = random.choice(settings.HOSTS)
        self.attacker_ip = "45.95.11.22"  # 模拟黑客常用 IP
        self.session_id = str(uuid.uuid4())

    def get_logs(self) -> list:
        logs = []
        # 1. 模拟 5-10 次失败登录
        fail_count = random.randint(5, 10)
        for attempt in range(fail_count):
            logs.append({
                "@timestamp": datetime.utcnow().isoformat() + "Z",
                "event.dataset": "host",
                "event.module": "endpoint",
                "event.category": "authentication",
                "event.type": "authentication",
                "event.action": "login_failed",
                "event.outcome": "failure",
                "event.reason": "Invalid credentials",
                "host.name": self.target_host,
                "host.id": str(uuid.uuid4()),
                "host.os.name": random.choice(["Windows", "Linux"]),
                "user.name": self.target_user,
                "user.id": f"S-1-5-21-{random.randint(100000000, 999999999)}-{random.randint(100000000, 999999999)}-{random.randint(100000000, 999999999)}-1001",
                "user.domain": random.choice(["CORP", "LOCAL"]),
                "source.ip": self.attacker_ip,
                "source.port": random.randint(49152, 65535),
                "source.geo.country_name": "China",
                "source.geo.country_iso_code": "CN",
                "destination.ip": random.choice(settings.INTERNAL_IPS),
                "destination.port": random.choice([22, 3389, 445]),
                "process.pid": random.randint(100, 1000),
                "process.name": random.choice(["sshd", "lsass.exe", "svchost.exe"]),
                "process.executable": "/usr/sbin/sshd" if "linux" in random.choice(["windows", "linux"]) else "C:\\Windows\\System32\\lsass.exe",
                "authentication.type": random.choice(["ssh", "rdp", "kerberos", "ntlm"]),
                "authentication.method": "password",
                "network.protocol": "tcp",
                "network.transport": "ssh" if random.random() > 0.5 else "rdp",
                "error.code": random.choice(["AUTH_FAILED", "INVALID_USER", "INVALID_CREDS"]),
                "error.message": "Authentication failed: invalid password",
                "event.duration": random.randint(1000, 5000),
                "session.id": self.session_id,
                "log.level": "warning",
                "message": f"Failed login attempt {attempt + 1}/{fail_count} for user {self.target_user}"
            })

        # 2. 紧接着一次成功登录 (触发告警的关键点)
        logs.append({
            "@timestamp": datetime.utcnow().isoformat() + "Z",
            "event.dataset": "host",
            "event.module": "endpoint",
            "event.category": "authentication",
            "event.type": "authentication",
            "event.action": "login_success",
            "event.outcome": "success",
            "event.reason": "Valid credentials",
            "host.name": self.target_host,
            "host.id": str(uuid.uuid4()),
            "host.os.name": random.choice(["Windows", "Linux"]),
            "user.name": self.target_user,
            "user.id": f"S-1-5-21-{random.randint(100000000, 999999999)}-{random.randint(100000000, 999999999)}-{random.randint(100000000, 999999999)}-1001",
            "user.domain": random.choice(["CORP", "LOCAL"]),
            "user.logon_type": random.choice(["RemoteInteractive", "Network", "Interactive"]),
            "source.ip": self.attacker_ip,
            "source.port": random.randint(49152, 65535),
            "source.geo.country_name": "China",
            "source.geo.country_iso_code": "CN",
            "destination.ip": random.choice(settings.INTERNAL_IPS),
            "destination.port": random.choice([22, 3389, 445]),
            "process.pid": random.randint(100, 1000),
            "process.name": random.choice(["sshd", "lsass.exe", "svchost.exe"]),
            "process.executable": "/usr/sbin/sshd" if "linux" in random.choice(["windows", "linux"]) else "C:\\Windows\\System32\\lsass.exe",
            "authentication.type": random.choice(["ssh", "rdp", "kerberos", "ntlm"]),
            "authentication.method": "password",
            "network.protocol": "tcp",
            "network.transport": "ssh" if random.random() > 0.5 else "rdp",
            "session.id": self.session_id,
            "session.duration": random.randint(300000, 3600000),  # ms
            "event.duration": random.randint(500, 2000),
            "risk_score": 85,
            "log.level": "critical",
            "message": f"Successful login after {fail_count} failed attempts - BRUTE FORCE DETECTED"
        })
        return logs
