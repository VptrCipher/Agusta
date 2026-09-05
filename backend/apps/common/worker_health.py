import json
import logging
import threading
from datetime import timedelta

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django_redis import get_redis_connection
from redis.exceptions import RedisError


logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL_SECONDS = 10
HEARTBEAT_STALE_SECONDS = 30
WORKER_HEALTH_KEY = "worker-health:v1:{worker_type}"
EXPECTED_WORKERS = (
    ("agentic-module", "Agentic Module Worker", "agentic-module-worker"),
    ("case-analysis", "Case Analysis Worker", "agentic-case-analysis-worker"),
    ("playbook", "Playbook Worker", "agentic-playbook-worker"),
    ("elk-action", "ELK Action Worker", "elk-action-worker"),
    ("dashboard-cache", "Dashboard Cache Worker", "dashboard-cache-worker"),
)


def _timestamp():
    return timezone.now().isoformat()


def _decode_hash(values):
    return {
        key.decode() if isinstance(key, bytes) else str(key): value.decode() if isinstance(value, bytes) else str(value)
        for key, value in values.items()
    }


class WorkerHealthReporter:
    def __init__(self, worker_type, *, redis_client=None, heartbeat_interval=HEARTBEAT_INTERVAL_SECONDS):
        self.worker_type = worker_type
        self.redis = redis_client or get_redis_connection("default")
        self.heartbeat_interval = heartbeat_interval
        self.stop_event = threading.Event()
        self.thread = None

    @property
    def key(self):
        return WORKER_HEALTH_KEY.format(worker_type=self.worker_type)

    def _write(self, **fields):
        try:
            self.redis.hset(self.key, mapping={key: str(value) for key, value in fields.items()})
        except RedisError as exc:
            logger.warning(
                "Worker health update failed: worker_type=%s error_type=%s",
                self.worker_type,
                type(exc).__name__,
            )

    def start(self):
        now = _timestamp()
        self._write(
            worker_type=self.worker_type,
            state="Starting",
            reason="",
            started_at=now,
            heartbeat_at=now,
            iteration_started_at="",
            last_iteration_success_at="",
            last_processed_at="",
            last_failure_at="",
            last_duration_ms="",
            last_message="",
            last_error="",
        )
        self.thread = threading.Thread(
            target=self._heartbeat_loop,
            name=f"{self.worker_type}-heartbeat",
            daemon=True,
        )
        self.thread.start()

    def _heartbeat_loop(self):
        while not self.stop_event.wait(self.heartbeat_interval):
            self._write(heartbeat_at=_timestamp())

    def iteration_started(self):
        now = _timestamp()
        self._write(
            state="Running",
            reason="",
            heartbeat_at=now,
            iteration_started_at=now,
        )

    def iteration_succeeded(self, result, duration_ms):
        now = _timestamp()
        fields = {
            "state": "Idle",
            "reason": "",
            "heartbeat_at": now,
            "iteration_started_at": "",
            "last_iteration_success_at": now,
            "last_duration_ms": max(0, int(duration_ms)),
            "last_message": result.message,
        }
        if result.processed:
            fields["last_processed_at"] = now
        self._write(**fields)

    def iteration_failed(self, exc, duration_ms):
        now = _timestamp()
        self._write(
            state="Degraded",
            reason="iteration_failed",
            heartbeat_at=now,
            iteration_started_at="",
            last_failure_at=now,
            last_duration_ms=max(0, int(duration_ms)),
            last_message="",
            last_error=json.dumps({
                "type": type(exc).__name__,
                "message": "Worker iteration failed.",
            }),
        )

    def stop(self):
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=1)
        self._write(
            state="Down",
            reason="graceful",
            heartbeat_at=_timestamp(),
            iteration_started_at="",
        )


def get_worker_health_states(*, redis_client=None, now=None):
    client = redis_client or get_redis_connection("default")
    current_time = now or timezone.now()
    stale_before = current_time - timedelta(seconds=HEARTBEAT_STALE_SECONDS)
    results = []

    for worker_type, display_name, log_role in EXPECTED_WORKERS:
        values = _decode_hash(client.hgetall(WORKER_HEALTH_KEY.format(worker_type=worker_type)))
        if not values:
            values = {
                "worker_type": worker_type,
                "state": "Down",
                "reason": "never_reported",
            }

        heartbeat_at = parse_datetime(values.get("heartbeat_at", ""))
        if values.get("state") != "Down" and (heartbeat_at is None or heartbeat_at < stale_before):
            values["state"] = "Down"
            values["reason"] = "heartbeat_expired"

        last_error = values.get("last_error", "")
        try:
            parsed_error = json.loads(last_error) if last_error else None
        except (TypeError, ValueError):
            parsed_error = {"type": "UnknownError", "message": "Worker iteration failed."}

        iteration_started_at = parse_datetime(values.get("iteration_started_at", ""))
        running_duration_seconds = None
        if values.get("state") == "Running" and iteration_started_at is not None:
            running_duration_seconds = max(0, int((current_time - iteration_started_at).total_seconds()))

        results.append({
            "worker_type": worker_type,
            "display_name": display_name,
            "state": values.get("state", "Down"),
            "reason": values.get("reason", ""),
            "started_at": values.get("started_at") or None,
            "heartbeat_at": values.get("heartbeat_at") or None,
            "iteration_started_at": values.get("iteration_started_at") or None,
            "last_iteration_success_at": values.get("last_iteration_success_at") or None,
            "last_processed_at": values.get("last_processed_at") or None,
            "last_failure_at": values.get("last_failure_at") or None,
            "last_duration_ms": int(values["last_duration_ms"]) if values.get("last_duration_ms") else None,
            "running_duration_seconds": running_duration_seconds,
            "last_message": values.get("last_message", ""),
            "last_error": parsed_error,
            "log_role": log_role,
        })

    return results
