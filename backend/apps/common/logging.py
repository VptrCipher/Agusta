import gzip
import json
import logging
import os
import shutil
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_MAX_BYTES = 10 * 1024 * 1024
LOG_BACKUP_COUNT = 10
LOG_ROLE_FILES = {
    "django": "django.log",
    "asgi": "asgi.log",
    "agentic-playbook-worker": "agentic-playbook-worker.log",
    "agentic-case-analysis-worker": "agentic-case-analysis-worker.log",
    "agentic-module-worker": "agentic-module-worker.log",
    "elk-action-worker": "elk-action-worker.log",
    "dashboard-cache-worker": "dashboard-cache-worker.log",
}
ROOT_PROCESS_FILE_LOGGERS = [""]
SERVER_PROCESS_FILE_LOGGERS = {
    "django": [
        "gunicorn.error",
        "gunicorn.access",
    ],
    "asgi": [
        "uvicorn",
        "uvicorn.access",
    ],
}
VERBOSE_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s:%(lineno)s] %(message)s"


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "message": record.getMessage(),
        }

        api_error = getattr(record, "api_error", None)
        if api_error is not None:
            payload["api_error"] = api_error

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False, default=str)


class GZipRotatingFileHandler(RotatingFileHandler):
    def __init__(self, filename, *args, **kwargs):
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        super().__init__(filename, *args, **kwargs)
        self.namer = lambda name: f"{name}.gz"
        self.rotator = self._gzip_rotator

    @staticmethod
    def _gzip_rotator(source, dest):
        if os.path.exists(dest):
            os.remove(dest)
        with open(source, "rb") as source_file:
            with gzip.open(dest, "wb") as dest_file:
                shutil.copyfileobj(source_file, dest_file)
        os.remove(source)


def log_dir(base_dir):
    return Path(base_dir) / "log"


def log_file_path(base_dir, role):
    filename = LOG_ROLE_FILES.get(role)
    if not filename:
        return None
    return log_dir(base_dir) / filename


def verbose_formatter():
    return logging.Formatter(VERBOSE_LOG_FORMAT)


def formatter_for_name(format_name):
    if str(format_name).lower() == "json":
        return JsonFormatter()
    return verbose_formatter()


def process_file_loggers(role):
    return ROOT_PROCESS_FILE_LOGGERS + SERVER_PROCESS_FILE_LOGGERS.get(role, [])


def configure_process_file_logging(role, *, base_dir=None, level=None, format_name=None):
    from django.conf import settings

    file_path = log_file_path(base_dir or settings.BASE_DIR, role)
    if file_path is None:
        return False

    marker = f"agusta-process-file:{role}"
    handler = None
    logger_names = process_file_loggers(role)
    for logger_name in logger_names:
        for existing in logging.getLogger(logger_name).handlers:
            if existing.get_name() == marker:
                handler = existing
                break
        if handler is not None:
            break

    if handler is None:
        handler = GZipRotatingFileHandler(
            file_path,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        handler.set_name(marker)
        handler.setLevel(level or getattr(settings, "LOG_LEVEL", "INFO"))
        handler.setFormatter(formatter_for_name(format_name or getattr(settings, "LOG_FORMAT", "text")))

    for logger_name in logger_names:
        target_logger = logging.getLogger(logger_name)
        if any(existing.get_name() == marker for existing in target_logger.handlers):
            continue
        target_logger.addHandler(handler)
    return True
