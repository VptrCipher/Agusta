"""Seed the AGUSTA demonstration environment.

Typical use:

    # first boot / fresh deployment (safe to re-run, no-op when present)
    python manage.py seed_demo_data

    # rebuild from scratch, removing only demo-marked records
    python manage.py seed_demo_data --reset

    # also push the bundled sample payloads through the real Module pipeline
    python manage.py seed_demo_data --replay-modules

    # remove the demonstration data and stop
    python manage.py seed_demo_data --purge
"""

from django.core.management.base import BaseCommand, CommandError

from apps.common.demo import DEMO_DATA_VERSION, loader, provenance, replay


class Command(BaseCommand):
    help = (
        "Create an interconnected demonstration SOC environment (cases, alerts, "
        "artifacts, enrichments, knowledge, playbook history). Idempotent."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Remove existing demo-marked records, then seed again.",
        )
        parser.add_argument(
            "--purge",
            action="store_true",
            help="Remove demo-marked records and exit without seeding.",
        )
        parser.add_argument(
            "--no-routine",
            action="store_true",
            help="Skip the lower-severity background queue.",
        )
        parser.add_argument(
            "--if-empty",
            action="store_true",
            help=(
                "Only seed when the deployment has no cases at all. Used for automatic "
                "first-boot seeding so an existing deployment with real data is never "
                "touched."
            ),
        )
        parser.add_argument(
            "--replay-modules",
            action="store_true",
            help=(
                "Additionally replay the bundled sample alert payloads through the "
                "real detection Modules, so some cases are produced by AGUSTA's own "
                "ingestion pipeline."
            ),
        )
        parser.add_argument(
            "--via-redis",
            action="store_true",
            help=(
                "With --replay-modules, publish payloads to the Redis streams and let "
                "the running module worker consume them, instead of invoking the "
                "Modules directly."
            ),
        )
        parser.add_argument(
            "--analyst-password",
            default="",
            help=(
                "Optional password for the demo analyst accounts. Omit to leave them "
                "unusable (recommended: sign in with your own superuser)."
            ),
        )

    def handle(self, *args, **options):
        if options["purge"] and options["reset"]:
            raise CommandError("Use either --purge or --reset, not both.")

        if options["purge"]:
            counts = loader.purge()
            self.stdout.write(self.style.WARNING(f"Purged demonstration data: {counts}"))
            return

        if options["reset"]:
            counts = loader.purge()
            self.stdout.write(f"Removed previous demonstration data: {counts}")

        if options["if_empty"]:
            from apps.cases.models import Case

            if Case.objects.exists():
                self.stdout.write(
                    "Deployment already contains cases; skipping automatic demonstration seeding."
                )
                return

        result = loader.seed(
            analyst_password=options["analyst_password"] or None,
            include_routine=not options["no_routine"],
        )

        if not result["created"]:
            self.stdout.write(
                self.style.WARNING(
                    "Demonstration environment already present, nothing to do. "
                    "Use --reset to rebuild it."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Seeded demonstration environment v{DEMO_DATA_VERSION}.")
            )

        for label in ("cases", "alerts", "artifacts", "enrichments", "knowledge", "playbooks", "case_relationships"):
            self.stdout.write(f"  {label:<20} {result.get(label, 0)}")

        if options["replay_modules"]:
            self.stdout.write("")
            self.stdout.write("Replaying bundled sample payloads through detection Modules...")
            replay_result = replay.replay_bundled_payloads(via_redis=options["via_redis"])
            for line in replay_result["log"]:
                self.stdout.write(f"  {line}")
            if replay_result["errors"]:
                self.stdout.write(
                    self.style.WARNING(f"  {len(replay_result['errors'])} payload(s) could not be replayed.")
                )

        self.stdout.write("")
        self.stdout.write(self.style.HTTP_INFO("Data provenance"))
        self.stdout.write(f"  {provenance.ATTRIBUTION}")
