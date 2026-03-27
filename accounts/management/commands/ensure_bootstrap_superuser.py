import os

from django.contrib.auth import get_user_model
from django.core.management import BaseCommand, CommandError


def _is_enabled(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Command(BaseCommand):
    help = "Create or update a bootstrap superuser when explicitly enabled via environment."

    def handle(self, *args, **options):
        if not _is_enabled(os.environ.get("DJANGO_BOOTSTRAP_SUPERUSER", "0")):
            self.stdout.write("Bootstrap superuser creation is disabled.")
            return

        username = os.environ.get("DJANGO_BOOTSTRAP_SUPERUSER_USERNAME", "").strip()
        password = os.environ.get("DJANGO_BOOTSTRAP_SUPERUSER_PASSWORD", "")
        email = os.environ.get("DJANGO_BOOTSTRAP_SUPERUSER_EMAIL", "").strip()

        if not username:
            raise CommandError("DJANGO_BOOTSTRAP_SUPERUSER_USERNAME is required.")
        if not password:
            raise CommandError("DJANGO_BOOTSTRAP_SUPERUSER_PASSWORD is required.")

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": True,
                "is_superuser": True,
            },
        )

        updated_fields = []
        if email and user.email != email:
            user.email = email
            updated_fields.append("email")

        if not user.is_staff:
            user.is_staff = True
            updated_fields.append("is_staff")

        if not user.is_superuser:
            user.is_superuser = True
            updated_fields.append("is_superuser")

        if hasattr(user, "role") and getattr(user, "role", "") != "admin":
            user.role = "admin"
            updated_fields.append("role")

        user.set_password(password)
        updated_fields.append("password")
        user.save(update_fields=list(dict.fromkeys(updated_fields)))

        if created:
            self.stdout.write(self.style.SUCCESS(f"Bootstrap superuser '{username}' created."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Bootstrap superuser '{username}' updated."))
