import logging

from django.core.management.base import BaseCommand

from apps.agentic.runtime.monitor import run_playbook_once
from apps.agentic.services.playbooks import recover_orphaned_playbook_runs
from apps.common.worker_runner import SLEEP_WHEN_IDLE, add_worker_arguments, run_worker

DEFAULT_INTERVAL_SECONDS = 3.0
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run the AGUSTA playbook worker."

    def add_arguments(self, parser):
        add_worker_arguments(parser, interval_help="Seconds to sleep when no playbook run is pending.")

    def handle(self, *args, **options):
        recovered = recover_orphaned_playbook_runs()
        if recovered:
            logger.warning("Recovered %d orphaned playbook run(s)", recovered)
        run_worker(
            self,
            options=options,
            worker_name="agentic playbook",
            worker_type="playbook",
            run_once=run_playbook_once,
            default_interval=DEFAULT_INTERVAL_SECONDS,
            sleep_policy=SLEEP_WHEN_IDLE,
            log_role="agentic-playbook-worker",
        )
