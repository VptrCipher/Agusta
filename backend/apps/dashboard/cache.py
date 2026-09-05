import logging

from django.core.cache import cache
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django_redis import get_redis_connection
from redis.exceptions import LockNotOwnedError


logger = logging.getLogger(__name__)

DASHBOARD_CACHE_KEY = "dashboard:overview:v1:{window}"
DASHBOARD_REFRESH_LOCK_KEY = "dashboard:overview:refresh:v1:{window}"
DASHBOARD_REFRESH_LOCK_TIMEOUT_SECONDS = 600
DASHBOARD_STALE_WARNING_INTERVALS = 3


def _cache_key(window):
    return DASHBOARD_CACHE_KEY.format(window=window)


def set_cached_dashboard_overview(window, overview, refresh_interval_seconds):
    cache.set(
        _cache_key(window),
        {
            "overview": overview,
            "refreshed_at": timezone.now().isoformat(),
            "refresh_interval_seconds": int(refresh_interval_seconds),
        },
        timeout=None,
    )


def get_cached_dashboard_overview(window):
    snapshot = cache.get(_cache_key(window))
    if snapshot is None:
        return None

    refreshed_at = parse_datetime(snapshot["refreshed_at"])
    if refreshed_at is None:
        raise ValueError(f"Invalid dashboard cache timestamp for window {window}.")

    refresh_interval_seconds = int(snapshot["refresh_interval_seconds"])
    age_seconds = max(0, int((timezone.now() - refreshed_at).total_seconds()))
    overview = dict(snapshot["overview"])
    overview["cache"] = {
        "generated_at": overview["generated_at"],
        "refreshed_at": refreshed_at.isoformat(),
        "refresh_interval_seconds": refresh_interval_seconds,
        "age_seconds": age_seconds,
        "stale_warning": age_seconds > refresh_interval_seconds * DASHBOARD_STALE_WARNING_INTERVALS,
    }
    return overview


def refresh_cached_dashboard_overview(window, refresh_interval_seconds):
    connection = get_redis_connection("default")
    lock = connection.lock(
        DASHBOARD_REFRESH_LOCK_KEY.format(window=window),
        timeout=DASHBOARD_REFRESH_LOCK_TIMEOUT_SECONDS,
        blocking_timeout=0,
    )
    if not lock.acquire(blocking=False):
        return False

    try:
        from .views import build_dashboard_overview

        overview = build_dashboard_overview(window)
        set_cached_dashboard_overview(window, overview, refresh_interval_seconds)
        return True
    finally:
        try:
            lock.release()
        except LockNotOwnedError:
            logger.warning("Dashboard refresh lock expired before release: window=%s", window)
