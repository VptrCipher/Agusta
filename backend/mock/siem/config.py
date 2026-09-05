import os
from pathlib import Path

from dotenv import load_dotenv

ENV_PATH = Path(__file__).with_name(".env")
load_dotenv(ENV_PATH, override=True)


def _bool_env(name, default=False):
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


ELK_ENABLED = _bool_env("MOCK_SIEM_ELK_ENABLED", False)
ELK_HOST = os.environ.get("MOCK_SIEM_ELK_HOST", "").rstrip("/")
ELK_KEY = os.environ.get("MOCK_SIEM_ELK_KEY", "")

SPLUNK_ENABLED = _bool_env("MOCK_SIEM_SPLUNK_ENABLED", False)
SPLUNK_HEC_URL = os.environ.get("MOCK_SIEM_SPLUNK_HEC_URL", "")
SPLUNK_TOKEN = os.environ.get("MOCK_SIEM_SPLUNK_TOKEN", "")


def validate_sender_config():
    missing = []
    if ELK_ENABLED:
        if not ELK_HOST:
            missing.append("MOCK_SIEM_ELK_HOST")
        if not ELK_KEY:
            missing.append("MOCK_SIEM_ELK_KEY")
    if SPLUNK_ENABLED:
        if not SPLUNK_HEC_URL:
            missing.append("MOCK_SIEM_SPLUNK_HEC_URL")
        if not SPLUNK_TOKEN:
            missing.append("MOCK_SIEM_SPLUNK_TOKEN")
    if missing:
        raise ValueError(f"Missing Mock SIEM configuration: {', '.join(missing)}")
