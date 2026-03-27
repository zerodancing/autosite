from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from catalog.models import Car, Service


class Order(models.Model):
    class OrderType(models.TextChoices):
        SERVICE = "service", _("Услуга")
        CAR = "car", _("Машина")

    class Status(models.TextChoices):
        PENDING = "pending", _("Ожидает обработки")
        CONFIRMED = "confirmed", _("Подтверждено")
        CANCELED = "canceled", _("Отменено")
        DONE = "done", _("Выполнено")

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    order_type = models.CharField(max_length=20, choices=OrderType.choices)

    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    car = models.ForeignKey(Car, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")

    scheduled_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Планируемое время"))
    customer_comment = models.TextField(blank=True, verbose_name=_("Комментарий"))

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Заказ")
        verbose_name_plural = _("Заказы")
        ordering = ("-created_at",)

    def clean(self):
        # Простой контроль согласованности.
        if self.order_type == self.OrderType.SERVICE and not self.service:
            raise models.ValidationError({"service": _("Для заказа услуги нужно указать услугу.")})
        if self.order_type == self.OrderType.CAR and not self.car:
            raise models.ValidationError({"car": _("Для заказа машины нужно указать машину.")})

    def __str__(self) -> str:
        if self.order_type == self.OrderType.SERVICE and self.service_id:
            return f"Заказ услуги: {self.service.title}"
        if self.order_type == self.OrderType.CAR and self.car_id:
            return f"Заказ машины: {self.car}"
        return f"Заказ #{self.pk}"
