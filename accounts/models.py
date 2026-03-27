from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        CLIENT = "client", _("Клиент")
        ADMIN = "admin", _("Администратор")
        SUPPORT = "support", _("Оператор поддержки")

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CLIENT)
    full_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=30, blank=True)

    def __str__(self) -> str:
        name = self.full_name.strip()
        return name if name else self.username
