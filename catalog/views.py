from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404, render

from .models import (
    Car,
    CarCategory,
    CarCharacteristicValue,
    CarImage,
    Service,
    ServiceCategory,
)


ORDERED_CAR_IMAGES = Prefetch("images", queryset=CarImage.objects.order_by("order", "id"))


def _cars_with_gallery():
    return Car.objects.select_related("category").prefetch_related(ORDERED_CAR_IMAGES)


def home(request):
    services = list(
        Service.objects.filter(is_active=True).select_related("category").order_by("-id")[:6]
    )
    cars = list(_cars_with_gallery().order_by("-id")[:6])

    service_categories = list(
        ServiceCategory.objects.annotate(
            item_count=Count("services", filter=Q(services__is_active=True))
        )
        .order_by("-item_count", "name")[:6]
    )
    car_categories = list(
        CarCategory.objects.annotate(item_count=Count("cars")).order_by("-item_count", "name")[:6]
    )
    brands = list(
        Car.objects.exclude(brand="")
        .order_by("brand")
        .values_list("brand", flat=True)
        .distinct()[:8]
    )

    return render(
        request,
        "catalog/home.html",
        {
            "services": services,
            "cars": cars,
            "featured_car": cars[0] if cars else None,
            "featured_service": services[0] if services else None,
            "service_categories": service_categories,
            "car_categories": car_categories,
            "brands": brands,
            "cars_total": Car.objects.count(),
            "services_total": Service.objects.filter(is_active=True).count(),
        },
    )


def services_list(request):
    q = request.GET.get("q", "").strip()
    category_slug = request.GET.get("category", "").strip()

    qs = Service.objects.filter(is_active=True).select_related("category")
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if category_slug:
        qs = qs.filter(category__slug=category_slug)

    categories = ServiceCategory.objects.all().order_by("name")
    return render(
        request,
        "catalog/services_list.html",
        {
            "services": qs.order_by("-id"),
            "categories": categories,
            "q": q,
            "category_slug": category_slug,
        },
    )


def service_detail(request, service_id: int):
    service = get_object_or_404(
        Service.objects.select_related("category"), pk=service_id, is_active=True
    )
    return render(request, "catalog/service_detail.html", {"service": service})


def cars_list(request):
    q = request.GET.get("q", "").strip()
    category_slug = request.GET.get("category", "").strip()
    year = request.GET.get("year", "").strip()

    qs = _cars_with_gallery()
    if q:
        qs = qs.filter(Q(brand__icontains=q) | Q(model__icontains=q) | Q(description__icontains=q))
    if category_slug:
        qs = qs.filter(category__slug=category_slug)
    if year.isdigit():
        qs = qs.filter(year=int(year))

    categories = CarCategory.objects.all().order_by("name")
    return render(
        request,
        "catalog/cars_list.html",
        {
            "cars": qs.order_by("-id"),
            "categories": categories,
            "q": q,
            "category_slug": category_slug,
            "year": year,
        },
    )


def car_detail(request, car_id: int):
    car = get_object_or_404(_cars_with_gallery(), pk=car_id)
    spec_values = (
        CarCharacteristicValue.objects.filter(car=car)
        .select_related("characteristic__group", "characteristic")
        .order_by("characteristic__group__order", "characteristic__name")
    )
    return render(request, "catalog/car_detail.html", {"car": car, "spec_values": spec_values})
