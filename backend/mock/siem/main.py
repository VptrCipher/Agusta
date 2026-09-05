import json
import random
import sys
import time
from pathlib import Path

import httpx

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from mock.siem import config, settings
from mock.siem.generator.cloud import CloudGenerator
from mock.siem.generator.host import HostGenerator
from mock.siem.generator.network import NetworkGenerator
from mock.siem.scenarios.cloud import CloudPrivilegeEscalationScenario
from mock.siem.scenarios.host import RansomwareScenario
from mock.siem.scenarios.network import BruteForceScenario


# --- 发送器类 (同步版本) ---
class ELKSender:
    def __init__(self):
        self.url = f"{config.ELK_HOST}/_bulk"
        self.headers = {
            "Content-Type": "application/x-ndjson",
            "Authorization": f"ApiKey {config.ELK_KEY}",
        }

    def send(self, batch, index_name):
        payload = ""
        for doc in batch:
            payload += json.dumps({"index": {"_index": index_name}}) + "\n"
            payload += json.dumps(doc) + "\n"

        with httpx.Client(verify=False, timeout=30.0, trust_env=False) as client:
            resp = client.post(
                self.url,
                content=payload,
                headers=self.headers
            )
            if resp.status_code >= 400:
                raise Exception(f"ELK Error: {resp.text}")


class SplunkSender:
    def __init__(self):
        self.url = config.SPLUNK_HEC_URL
        self.headers = {"Authorization": f"Splunk {config.SPLUNK_TOKEN}"}

    def send(self, batch, index_name):
        payload = "".join([json.dumps({"event": doc, "index": index_name}) for doc in batch])
        with httpx.Client(verify=False, timeout=30.0, trust_env=False) as client:
            resp = client.post(self.url, content=payload, headers=self.headers)
            if resp.status_code >= 400:
                raise Exception(f"Splunk Error: {resp.text}")


# --- 核心引擎 ---
def run_engine(generators, senders, scenario_mapping=None):
    """
    generators: dict { index_name: generator_instance }
    senders: list [sender_instances]
    scenario_mapping: dict { index_name: [scenario_classes] }
    """
    print(f"Simulation engine started. Targets: {[s.__class__.__name__ for s in senders]}")

    while True:
        for index_name, gen in generators.items():
            # 1. 生成基础批次
            batch = [gen.generate() for _ in range(settings.BATCH_SIZE)]

            # 2. 注入对应索引的异常场景
            if scenario_mapping and index_name in scenario_mapping and random.random() < settings.MALICIOUS_PERCENTAGE:
                scenario_class = random.choice(scenario_mapping[index_name])
                scenario_instance = scenario_class()
                batch.extend(scenario_instance.get_logs())

            # 3. 同步发送到所有目标（带重试）
            for attempt in range(3):
                try:
                    for s in senders:
                        s.send(batch, index_name)
                    break
                except Exception as e:
                    wait = 2 ** (attempt + 1)
                    print(f"[WARN] Send attempt {attempt+1}/3 failed: {e}. Retrying in {wait}s...")
                    time.sleep(wait)
            else:
                print(f"[ERROR] Send failed after 3 attempts, skipping batch for {index_name}.")

        # 控制频率 (简单 Sleep)
        time.sleep(settings.BATCH_SIZE / settings.EPS)


def build_generators():
    return {
        settings.NET_INDEX: NetworkGenerator(),
        settings.HOST_INDEX: HostGenerator(),
        settings.CLOUD_INDEX: CloudGenerator(),
    }

def build_senders():
    config.validate_sender_config()
    senders = []
    if config.ELK_ENABLED:
        senders.append(ELKSender())
    if config.SPLUNK_ENABLED:
        senders.append(SplunkSender())
    return senders

def build_scenario_mapping():
    return {
        settings.NET_INDEX: [BruteForceScenario],
        settings.HOST_INDEX: [RansomwareScenario],
        settings.CLOUD_INDEX: [CloudPrivilegeEscalationScenario],
    }

def main():
    my_generators = build_generators()
    my_senders = build_senders()
    my_scenario_mapping = build_scenario_mapping()

    if not my_senders:
        raise RuntimeError("No senders configured. Please check mock/siem/.env")

    run_engine(
        generators=my_generators,
        senders=my_senders,
        scenario_mapping=my_scenario_mapping
    )


if __name__ == "__main__":
    main()
