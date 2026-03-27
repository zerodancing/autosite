from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import Order


class BaseOrderForm(forms.ModelForm):
    customer_comment = forms.CharField(
        required=False,
        max_length=2000,
        label=_("Комментарий"),
        widget=forms.Textarea(
            attrs={
                "rows": 5,
                "class": "mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 outline-none focus:border-slate-400",
            }
        ),
    )

    class Meta:
        model = Order
        fields = ("customer_comment",)

    def clean_customer_comment(self):
        return (self.cleaned_data.get("customer_comment") or "").strip()


class ServiceOrderForm(BaseOrderForm):
    scheduled_at = forms.DateTimeField(
        required=False,
        input_formats=["%Y-%m-%dT%H:%M"],
        label=_("Желаемое время (опционально)"),
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={
                "type": "datetime-local",
                "class": "mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 outline-none focus:border-slate-400",
            },
        ),
    )

    class Meta(BaseOrderForm.Meta):
        fields = ("scheduled_at", "customer_comment")

    def clean_scheduled_at(self):
        scheduled_at = self.cleaned_data.get("scheduled_at")
        if not scheduled_at:
            return None

        if timezone.is_naive(scheduled_at):
            scheduled_at = timezone.make_aware(scheduled_at, timezone.get_current_timezone())

        if scheduled_at < timezone.now():
            raise forms.ValidationError(_("Нельзя выбрать время в прошлом."))

        return scheduled_at

    def save_order(self, *, user, service):
        order = Order(
            user=user,
            order_type=Order.OrderType.SERVICE,
            service=service,
            scheduled_at=self.cleaned_data.get("scheduled_at"),
            customer_comment=self.cleaned_data.get("customer_comment", ""),
            total_price=service.price_from,
            status=Order.Status.PENDING,
        )
        order.full_clean()
        order.save()
        return order


class CarOrderForm(BaseOrderForm):
    class Meta(BaseOrderForm.Meta):
        fields = ("customer_comment",)

    def save_order(self, *, user, car):
        order = Order(
            user=user,
            order_type=Order.OrderType.CAR,
            car=car,
            customer_comment=self.cleaned_data.get("customer_comment", ""),
            total_price=car.price,
            status=Order.Status.PENDING,
        )
        order.full_clean()
        order.save()
        return order
