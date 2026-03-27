from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Upload files from MEDIA_ROOT to the configured default storage backend."

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Overwrite files that already exist in the configured storage.",
        )

    def handle(self, *args, **options):
        media_root = Path(settings.MEDIA_ROOT)
        if not media_root.exists():
            raise CommandError(f"MEDIA_ROOT does not exist: {media_root}")

        storage_location = getattr(default_storage, "location", None)
        if storage_location:
            try:
                if Path(storage_location).resolve() == media_root.resolve():
                    raise CommandError(
                        "Default storage still points to the local MEDIA_ROOT. "
                        "Configure remote production storage before running this command."
                    )
            except OSError:
                pass

        local_files = sorted(path for path in media_root.rglob("*") if path.is_file())
        if not local_files:
            self.stdout.write(self.style.WARNING(f"No files found in {media_root}"))
            return

        uploaded = 0
        skipped = 0
        overwrite = options["overwrite"]

        for local_path in local_files:
            relative_path = local_path.relative_to(media_root).as_posix()

            if default_storage.exists(relative_path):
                if not overwrite:
                    skipped += 1
                    self.stdout.write(f"Skipped existing: {relative_path}")
                    continue
                default_storage.delete(relative_path)

            with local_path.open("rb") as file_handle:
                default_storage.save(relative_path, File(file_handle, name=relative_path))
            uploaded += 1
            self.stdout.write(f"Uploaded: {relative_path}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Media sync completed. Uploaded: {uploaded}. Skipped: {skipped}."
            )
        )
