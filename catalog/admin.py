from django.contrib import admin
from django.db import connection
from django.utils.html import format_html

from .forms import CarAdminForm, ServiceAdminForm, save_car_gallery, save_service_image
from .models import (
    Car,
    CarImage,
    CarCategory,
    CarCharacteristic,
    CarCharacteristicGroup,
    CarCharacteristicValue,
    Service,
    ServiceCategory,
    SiteMetric,
)
from .utils import resolve_uploaded_media_url


class AdminImageExperienceMixin:
    class Media:
        css = {"all": ("catalog/admin/image-upload.css",)}
        js = ("catalog/admin/image-upload.js",)


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Service)
class ServiceAdmin(AdminImageExperienceMixin, admin.ModelAdmin):
    form = ServiceAdminForm
    list_display = ("title", "category", "price_from", "duration_minutes", "is_active")
    list_filter = ("is_active", "category")
    search_fields = ("title", "description")
    readonly_fields = ("image_preview",)
    fieldsets = (
        ("Основное", {"fields": ("category", "title", "description")}),
        ("Стоимость и публикация", {"fields": ("price_from", "duration_minutes", "is_active")}),
        ("Изображение", {"fields": ("image_preview", "image_url", "image_upload")}),
    )

    @admin.display(description="Текущее изображение")
    def image_preview(self, obj):
        if not obj or not obj.image_url:
            return "Изображение пока не добавлено."
        return format_html(
            '<div class="admin-image-preview-card"><img src="{}" alt="{}"><div>{}</div></div>',
            resolve_uploaded_media_url(obj.image_url),
            obj.title,
            obj.image_url,
        )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        uploaded_image = form.cleaned_data.get("image_upload")
        if uploaded_image:
            obj.image_url = save_service_image(obj, uploaded_image)
            obj.save(update_fields=["image_url"])


@admin.register(CarCategory)
class CarCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Car)
class CarAdmin(AdminImageExperienceMixin, admin.ModelAdmin):
    form = CarAdminForm
    list_display = ("brand", "model", "year", "price", "mileage_km", "is_active")
    list_filter = ("is_active", "category", "year")
    search_fields = ("brand", "model", "description")
    fieldsets = (
        (
            "Карточка автомобиля",
            {
                "fields": (
                    "category",
                    ("brand", "model"),
                    ("year", "price"),
                    ("mileage_km", "fuel_type"),
                    ("transmission", "color"),
                    "description",
                    "is_active",
                )
            },
        ),
        (
            "Изображения",
            {
                "description": "1. Добавьте новые фото в зону ниже. 2. Сохраните машину. 3. Уже сохранённые изображения можно переставлять местами и удалять в блоке ниже.",
                "fields": ("gallery_uploads",),
            },
        ),
    )

    class CarImageInline(admin.StackedInline):
        model = CarImage
        extra = 0
        verbose_name = "Изображение галереи"
        verbose_name_plural = "Текущая галерея и порядок"
        readonly_fields = ("preview",)
        fields = ("preview", "image", "order", "alt_text")
        ordering = ("order", "id")

        @admin.display(description="Превью")
        def preview(self, obj):
            if not obj or not getattr(obj, "image", None):
                return "Изображение появится после сохранения."
            return format_html(
                '<div class="admin-inline-image-card"><img src="{}" alt="{}"></div>',
                obj.image_url,
                obj.alt_text or obj.image.name,
            )

    class CarCharacteristicValueInline(admin.TabularInline):
        model = CarCharacteristicValue
        extra = 0
        fields = ("characteristic", "value_int", "value_decimal", "value_bool", "value_text", "value_enum")

    inlines = [CarImageInline, CarCharacteristicValueInline]

    def get_inlines(self, request, obj):
        try:
            tables = connection.introspection.table_names()
        except Exception:
            tables = []

        inlines = [self.CarCharacteristicValueInline]
        if CarImage._meta.db_table in tables:
            inlines.insert(0, self.CarImageInline)
        return inlines

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        uploaded_files = form.cleaned_data.get("gallery_uploads") or []

        if uploaded_files:
            obj.image_url = save_car_gallery(obj, uploaded_files)
            obj.save(update_fields=["image_url"])


@admin.register(CarCharacteristicGroup)
class CarCharacteristicGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("order",)
    search_fields = ("name", "slug")


@admin.register(CarCharacteristic)
class CarCharacteristicAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "group", "value_type", "unit")
    list_filter = ("group", "value_type")
    search_fields = ("name", "slug", "group__name")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(SiteMetric)
class SiteMetricAdmin(admin.ModelAdmin):
    list_display = ("id", "total_visits", "updated_at")
    readonly_fields = ("total_visits", "updated_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
