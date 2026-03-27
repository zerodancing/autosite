from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from catalog.models import Car, Service
from .forms import CarOrderForm, ServiceOrderForm
from .models import Order


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "orders/my_orders.html", {"orders": orders})


@login_required
def create_service_order(request, service_id: int):
    service = get_object_or_404(Service, pk=service_id, is_active=True)
    form = ServiceOrderForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        order = form.save_order(user=request.user, service=service)
        return redirect("orders:order_detail", order_id=order.pk)

    return render(
        request,
        "orders/create_service_order.html",
        {"service": service, "form": form},
    )


@login_required
def create_car_order(request, car_id: int):
    car = get_object_or_404(Car, pk=car_id, is_active=True)
    form = CarOrderForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        order = form.save_order(user=request.user, car=car)
        return redirect("orders:order_detail", order_id=order.pk)

    return render(request, "orders/create_car_order.html", {"car": car, "form": form})


@login_required
def order_detail(request, order_id: int):
    order = get_object_or_404(Order, pk=order_id)
    if order.user_id != request.user.id and not request.user.is_staff:
        raise Http404()
    return render(request, "orders/order_detail.html", {"order": order})
