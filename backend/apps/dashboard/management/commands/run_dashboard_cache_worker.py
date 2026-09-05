import logging
import time

from django.core.management.base import BaseCommand

from apps.common.worker_runner import SLEEP_ALWAYS, WorkerIterationResult, add_worker_arguments, run_worker
from apps.dashboard.cache import refresh_cached_dashboard_overview
from apps.dashboard.views import WINDOW_DELTAS
from apps.settings.runtime_config import get_dashboard_refresh_interval_seconds


logger = logging.getLogger(__name__)

DASHBOARD_REFRESH_WARNING_SECONDS = 60


class Command(BaseCommand):
    help = "Refresh the Redis-backed dashboard overview cache."

    def add_arguments(self, parser):
        add_worker_arguments(
            parser,
            interval_help="Seconds between refreshes. Defaults to the Runtime Settings value.",
        )

    def handle(self, *args, **options):
        next_sleep_seconds = None

        def effective_interval():
            return options["interval"] or get_dashboard_refresh_interval_seconds()

        def refresh_once():
            nonlocal next_sleep_seconds
            interval = effective_interval()
            started = time.perf_counter()
            refreshed = []
            skipped = []
            failed = []

            for window in WINDOW_DELTAS:
                window_started = time.perf_counter()
                try:
                    if refresh_cached_dashboard_overview(window, interval):
                        refreshed.append(window)
                        logger.info(
                            "Dashboard cache refreshed: window=%s duration_ms=%.2f",
                            window,
                            (time.perf_counter() - window_started) * 1000,
                        )
                    else:
                        skipped.append(window)
                        logger.info("Dashboard cache refresh skipped because lock is held: window=%s", window)
                except Exception as exc:  # noqa: BLE001 - each window refresh must fail independently.
                    failed.append(window)
                    logger.exception("Dashboard cache refresh failed: window=%s error=%s", window, exc)

            duration_seconds = time.perf_counter() - started
            if duration_seconds > DASHBOARD_REFRESH_WARNING_SECONDS:
                logger.warning(
                    "Dashboard cache refresh exceeded target: duration_seconds=%.2f target_seconds=%s",
                    duration_seconds,
                    DASHBOARD_REFRESH_WARNING_SECONDS,
                )
            next_sleep_seconds = min(60, interval) if failed else interval
            if failed:
                raise RuntimeError("Dashboard cache refresh failed.")

            return WorkerIterationResult(
                processed=bool(refreshed),
                message=(
                    f"Dashboard cache refresh completed in {duration_seconds:.2f}s; "
                    f"refreshed={','.join(refreshed) or 'none'}; "
                    f"skipped={','.join(skipped) or 'none'}; "
                    f"failed={','.join(failed) or 'none'}."
                ),
            )

        run_worker(
            self,
            options=options,
            worker_name="dashboard cache",
            worker_type="dashboard-cache",
            run_once=refresh_once,
            default_interval=get_dashboard_refresh_interval_seconds,
            sleep_policy=SLEEP_ALWAYS,
            sleep_seconds=lambda: next_sleep_seconds or effective_interval(),
            log_role="dashboard-cache-worker",
        )
