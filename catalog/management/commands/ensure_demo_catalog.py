import os
from pathlib import Path

from django.core.management import BaseCommand, CommandError, call_command

from catalog.models import Car


def _is_enabled(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Command(BaseCommand):
    help = "Load the demo catalog fixture into an empty database when explicitly enabled."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Load the fixture even if cars already exist.",
        )

    def handle(self, *args, **options):
        enabled = _is_enabled(os.environ.get("DJANGO_LOAD_DEMO_FIXTURE", "0"))
        force = options["force"]

        if not enabled and not force:
            self.stdout.write("Demo catalog loading is disabled.")
            return

        if Car.objects.exists() and not force:
            self.stdout.write("Cars already exist. Demo catalog fixture skipped.")
            return

        fixture_path = Path("catalog/fixtures/catalog_demo_seed.json")
        if not fixture_path.exists():
            raise CommandError(f"Fixture not found: {fixture_path}")

        call_command("loaddata", fixture_path.as_posix())
        self.stdout.write(self.style.SUCCESS("Demo catalog fixture loaded."))
