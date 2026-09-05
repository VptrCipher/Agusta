from datetime import UTC

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.common.worker_runner import SLEEP_ALWAYS, WorkerIterationResult, add_worker_arguments, run_worker
from apps.webhook.elk_actions import ELKActionProcessor


def parse_cli_datetime(value):
    if not value:
        return None
    parsed = parse_datetime(value)
    if parsed is None:
        raise CommandError(f"Invalid datetime: {value}")
    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed, UTC)
    return parsed


class Command(BaseCommand):
    help = "Run the ELK action index worker and write alert hits into Redis streams."

    def add_arguments(self, parser):
        parser.add_argument("--index", help="ELK action index name. Defaults to the Settings UI value.")
        add_worker_arguments(parser, interval_help="Polling interval in seconds. Defaults to the Settings UI value.")
        parser.add_argument("--size", type=int, help="Maximum ELK action documents to read per poll. Defaults to the Settings UI value.")
        parser.add_argument("--start-time", help="Initial lower bound for @timestamp, e.g. 2026-06-23T00:00:00Z.")

    def handle(self, *args, **options):
        if options["size"] is not None and options["size"] <= 0:
            raise CommandError("--size must be greater than 0.")

        processor = ELKActionProcessor(index_name=options["index"], interval_seconds=options["interval"], size=options["size"])
        start_time = parse_cli_datetime(options.get("start_time"))

        def process_once():
            nonlocal start_time
            result = processor.process_once(start_time=start_time)
            start_time = None
            return WorkerIterationResult(
                processed=bool(result.actions or result.sent),
                message=f"Processed {result.actions} ELK action(s); sent {result.sent} Redis message(s); skipped {result.skipped} hit(s).",
            )

        run_worker(
            self,
            options=options,
            worker_name="ELK action",
            worker_type="elk-action",
            run_once=process_once,
            default_interval=lambda: processor.interval_seconds,
            sleep_policy=SLEEP_ALWAYS,
            started_message=f"ELK action worker started; polling {processor.index_name} every {processor.interval_seconds}s",
            stopped_message="ELK action worker stopped.",
            sleep_seconds=lambda: processor.interval_seconds,
            log_role="elk-action-worker",
        )
