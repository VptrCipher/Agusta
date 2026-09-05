import random
import uuid
from datetime import datetime

from mock.siem import settings


class RansomwareScenario(object):
    def __init__(self):
        self.target_host = random.choice(settings.HOSTS)
        self.target_user = random.choice(settings.USERS)
        self.malware_proc = "decryptor.exe"

        self.malware_pid = random.randint(1000, 9999)
        self.malware_hash = uuid.uuid4().hex

    def get_logs(self) -> list:
        logs = []
        base_path = f"C:\\Users\\{self.target_user}\\Documents\\"

        # 1. 模拟删除卷影副本 (Shadow Copy) - 典型的勒索预兆
        logs.append({
            "@timestamp": datetime.utcnow().isoformat() + "Z",
            "event.dataset": "host",
            "event.module": "endpoint",
            "event.category": "process",
            "event.type": "process_started",
            "event.action": "process_started",
            "event.outcome": "success",
            "host.name": self.target_host,
            "host.id": str(uuid.uuid4()),
            "host.os.name": "Windows",
            "user.name": self.target_user,
            "user.id": f"S-1-5-21-{random.randint(100000000, 999999999)}-{random.randint(100000000, 999999999)}-{random.randint(100000000, 999999999)}-1001",
            "process.pid": random.randint(100, 1000),
            "process.name": "vssadmin.exe",
            "process.command_line": "vssadmin.exe delete shadows /all /quiet",
            "process.executable": "C:\\Windows\\System32\\vssadmin.exe",
            "process.hash.md5": uuid.uuid4().hex[:32],
            "process.hash.sha256": uuid.uuid4().hex,
            "process.parent.name": random.choice(["cmd.exe", "powershell.exe"]),
            "process.parent.pid": random.randint(100, 1000),
            "process.working_directory": "C:\\Windows\\System32",
            "event.duration": random.randint(100, 5000),
            "log.level": "critical",
            "risk_score": 100,
            "message": "Shadow Copy deletion detected - ransomware indicator"
        })

        # 2. 批量生成文件重命名日志 (模拟加密过程)
        extensions = [".docx", ".pdf", ".jpg", ".xlsx", ".ppt", ".xls"]
        for i in range(20):
            original_file = f"finance_data_{i}{random.choice(extensions)}"
            encrypted_file = f"{original_file}.encrypted"
            logs.append({
                "@timestamp": datetime.utcnow().isoformat() + "Z",
                "event.dataset": "host",
                "event.module": "endpoint",
                "event.category": "file",
                "event.type": "file_renamed",
                "event.action": "file_renamed",
                "event.outcome": "success",
                "host.name": self.target_host,
                "host.id": str(uuid.uuid4()),
                "host.os.name": "Windows",
                "user.name": self.target_user,
                "user.id": f"S-1-5-21-{random.randint(100000000, 999999999)}-{random.randint(100000000, 999999999)}-{random.randint(100000000, 999999999)}-1001",
                "file.name": original_file,
                "file.path": base_path + original_file,
                "file.target_path": base_path + encrypted_file,
                "file.size": random.randint(1024, 10485760),  # 1KB to 10MB
                "file.hash.md5": uuid.uuid4().hex[:32],
                "file.hash.sha256": uuid.uuid4().hex,
                "file.extension": random.choice(extensions),
                "process.pid": self.malware_pid,
                "process.name": self.malware_proc,
                "process.executable": f"C:\\Users\\{self.target_user}\\AppData\\Roaming\\{self.malware_proc}",
                "process.hash.md5": self.malware_hash[:32],
                "process.hash.sha256": self.malware_hash,
                "process.parent.name": "explorer.exe",
                "process.parent.pid": random.randint(100, 1000),
                "log.level": "warning",
                "risk_score": 95,
                "message": f"File encrypted by {self.malware_proc}: {original_file}"
            })

        # 3. 留下勒索说明文件
        logs.append({
            "@timestamp": datetime.utcnow().isoformat() + "Z",
            "event.dataset": "host",
            "event.module": "endpoint",
            "event.category": "file",
            "event.type": "file_created",
            "event.action": "file_created",
            "event.outcome": "success",
            "host.name": self.target_host,
            "host.id": str(uuid.uuid4()),
            "host.os.name": "Windows",
            "user.name": self.target_user,
            "user.id": f"S-1-5-21-{random.randint(100000000, 999999999)}-{random.randint(100000000, 999999999)}-{random.randint(100000000, 999999999)}-1001",
            "file.name": "README_TO_DECRYPT.txt",
            "file.path": base_path + "README_TO_DECRYPT.txt",
            "file.size": random.randint(512, 2048),
            "file.hash.md5": uuid.uuid4().hex[:32],
            "file.hash.sha256": uuid.uuid4().hex,
            "file.content": "Your files have been encrypted. Contact us for decryption key.",
            "process.pid": self.malware_pid,
            "process.name": self.malware_proc,
            "process.executable": f"C:\\Users\\{self.target_user}\\AppData\\Roaming\\{self.malware_proc}",
            "process.hash.md5": self.malware_hash[:32],
            "process.hash.sha256": self.malware_hash,
            "process.parent.name": "explorer.exe",
            "process.parent.pid": random.randint(100, 1000),
            "event.duration": random.randint(100, 5000),
            "log.level": "critical",
            "risk_score": 100,
            "message": "Ransomware ransom note created"
        })
        return logs
