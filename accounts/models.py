from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from .normalization import normalize_email, normalize_phone


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        CLIENT = "client", _("Клиент")
        ADMIN = "admin", _("Администратор")
        SUPPORT = "support", _("Оператор поддержки")

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CLIENT)
    full_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=30, blank=True)

    def save(self, *args, **kwargs):
        self.email = normalize_email(self.email)
        self.phone = normalize_phone(self.phone)
        self.full_name = (self.full_name or "").strip()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        name = self.full_name.strip()
        return name if name else self.username
