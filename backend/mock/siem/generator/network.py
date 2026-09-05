import random
from datetime import datetime

from mock.siem import settings


class NetworkGenerator:
    # 常见端口和协议
    PORTS_CONFIG = [
        {"port": 443, "proto": "tcp", "action": "allow", "service": "https", "weight": 35},
        {"port": 80, "proto": "tcp", "action": "allow", "service": "http", "weight": 20},
        {"port": 22, "proto": "tcp", "action": "deny", "service": "ssh", "weight": 15},
        {"port": 3389, "proto": "tcp", "action": "allow", "service": "rdp", "weight": 10},
        {"port": 3306, "proto": "tcp", "action": "allow", "service": "mysql", "weight": 8},
        {"port": 5432, "proto": "tcp", "action": "allow", "service": "postgresql", "weight": 7},
        {"port": 6379, "proto": "tcp", "action": "allow", "service": "redis", "weight": 3},
        {"port": 53, "proto": "udp", "action": "allow", "service": "dns", "weight": 2},
    ]

    @classmethod
    def generate(cls):
        p = random.choices(cls.PORTS_CONFIG, weights=[x["weight"] for x in cls.PORTS_CONFIG])[0]
        src_ip = random.choice(settings.INTERNAL_IPS)
        dst_ip = random.choice(settings.EXTERNAL_IPS)

        # 数据字节数
        bytes_in = random.randint(100, 1000000)
        bytes_out = random.randint(100, 500000)

        return {
            "@timestamp": datetime.utcnow().isoformat() + "Z",
            "event.dataset": "network",
            "event.module": "firewall",
            "event.category": "network_traffic",
            "event.type": "connection",
            "event.action": p["action"],
            "event.outcome": "success" if p["action"] == "allow" else "failure",
            "network.protocol": p["proto"],
            "network.direction": "egress",
            "source.ip": src_ip,
            "source.port": random.randint(49152, 65535),
            "source.mac": f"{random.randint(0, 255):02x}:{random.randint(0, 255):02x}:{random.randint(0, 255):02x}:{random.randint(0, 255):02x}:{random.randint(0, 255):02x}:{random.randint(0, 255):02x}",
            "destination.ip": dst_ip,
            "destination.port": p["port"],
            "destination.service": p["service"],
            "network.bytes_in": bytes_in,
            "network.bytes_out": bytes_out,
            "network.packets": random.randint(1, 10000),
            "network.duration": random.randint(100, 3600000),  # ms
            "host.name": random.choice(settings.HOSTS),
            "host.ip": src_ip,
            "process.pid": random.randint(100, 65535),
            "process.name": random.choice(settings.PROCESSES),
            "user.name": random.choice(settings.USERS),
            "user.id": f"{random.randint(1000, 9999)}",
            "firewall.rule_id": f"FW-{random.randint(10000, 99999)}",
            "firewall.rule_name": f"rule-{random.choice(['allow', 'deny'])}-traffic",
            "log.level": "info"
        }
