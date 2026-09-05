import random
import uuid
from datetime import datetime

from mock.siem import settings


class HostGenerator:
    # 常见进程动作
    PROCESS_ACTIONS = [
        {"action": "process_created", "weight": 50},
        {"action": "process_terminated", "weight": 20},
        {"action": "file_created", "weight": 15},
        {"action": "file_deleted", "weight": 10},
        {"action": "network_connection", "weight": 3},
        {"action": "registry_modified", "weight": 2},
    ]

    FILE_EXTENSIONS = [".exe", ".dll", ".sys", ".log", ".txt", ".dat", ".tmp", ".cmd", ".ps1", ".sh"]

    @classmethod
    def generate(cls):
        host_name = random.choice(settings.HOSTS)
        user_name = random.choice(settings.USERS)
        action_obj = random.choices(cls.PROCESS_ACTIONS, weights=[x["weight"] for x in cls.PROCESS_ACTIONS])[0]
        action = action_obj["action"]
        process_name = random.choice(settings.PROCESSES)

        return {
            "@timestamp": datetime.utcnow().isoformat() + "Z",
            "event.dataset": "host",
            "event.module": "endpoint",
            "event.category": "process" if "process" in action else "file",
            "event.type": action,
            "event.action": action,
            "event.outcome": random.choice(["success", "failure"]),
            "host.name": host_name,
            "host.id": str(uuid.uuid4()),
            "host.os.name": random.choice(["Windows", "Linux", "macOS"]),
            "host.os.version": random.choice(["10", "11", "20.04", "22.04", "12.0"]),
            "host.architecture": random.choice(["x86_64", "arm64"]),
            "user.name": user_name,
            "user.id": f"S-1-5-21-{random.randint(1000000000, 9999999999)}-{random.randint(1000000000, 9999999999)}-{random.randint(1000000000, 9999999999)}-{random.randint(500, 9999)}",
            "user.domain": random.choice(["CORP", "LOCAL", "WORKGROUP"]),
            "process.pid": random.randint(100, 65535),
            "process.ppid": random.randint(100, 65535),
            "process.name": process_name,
            "process.executable": f"/usr/bin/{process_name}" if "." not in process_name else f"C:\\Windows\\System32\\{process_name}",
            "process.command_line": f"{process_name} {random.choice(['--verbose', '-d', '--config', ''])}",
            "process.hash.md5": f"{uuid.uuid4().hex[:32]}",
            "process.hash.sha256": f"{uuid.uuid4().hex}",
            "process.parent.name": random.choice(["svchost.exe", "bash", "systemd"]),
            "process.parent.pid": random.randint(100, 1000),
            "file.name": f"file_{random.randint(1000, 9999)}{random.choice(cls.FILE_EXTENSIONS)}",
            "file.path": f"/var/log/app.log" if "linux" in random.choice(["windows", "linux"]) else f"C:\\Users\\{user_name}\\Documents\\file.txt",
            "file.size": random.randint(1024, 10485760),  # 1KB to 10MB
            "file.hash.md5": f"{uuid.uuid4().hex[:32]}",
            "file.hash.sha256": f"{uuid.uuid4().hex}",
            "log.level": random.choice(["info", "warning", "error"]),
            "message": f"Process {process_name} executed by user {user_name}",
        }
