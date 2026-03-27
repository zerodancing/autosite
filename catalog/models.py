from django.core.exceptions import ValidationError
from django.db import models
from django.db.utils import OperationalError, ProgrammingError
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from .utils import resolve_uploaded_media_url


class ServiceCategory(models.Model):
    name = models.CharField(max_length=120, verbose_name=_("Категория услуг"))
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Категория услуг")
        verbose_name_plural = _("Категории услуг")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class CarImage(models.Model):
    car = models.ForeignKey("Car", on_delete=models.CASCADE, related_name="images", verbose_name=_("Машина"))
    image = models.FileField(upload_to="cars/%Y/%m/", verbose_name=_("Изображение"))
    order = models.PositiveIntegerField(default=0, verbose_name=_("Порядок"))
    alt_text = models.CharField(max_length=200, blank=True, verbose_name=_("Альтернативный текст"))

    class Meta:
        verbose_name = _("Изображение машины")
        verbose_name_plural = _("Изображения машин")
        ordering = ["order"]

    def __str__(self):
        return f"{self.car}: {self.image.name}"

    @property
    def image_url(self) -> str:
        try:
            return self.image.url
        except Exception:
            return resolve_uploaded_media_url(self.image.name)


class Service(models.Model):
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name="services")
    title = models.CharField(max_length=200, verbose_name=_("Название услуги"))
    description = models.TextField(verbose_name=_("Описание"))
    price_from = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("Цена от"))
    duration_minutes = models.PositiveIntegerField(default=60, verbose_name=_("Длительность (мин)"))
    image_url = models.URLField(blank=True, verbose_name=_("Изображение (URL)"))
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Услуга")
        verbose_name_plural = _("Услуги")

    def __str__(self) -> str:
        return self.title


class CarCategory(models.Model):
    name = models.CharField(max_length=120, verbose_name=_("Категория машин"))
    slug = models.SlugField(max_length=140, unique=True)

    class Meta:
        verbose_name = _("Категория машин")
        verbose_name_plural = _("Категории машин")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class Car(models.Model):
    category = models.ForeignKey(CarCategory, on_delete=models.CASCADE, related_name="cars")
    brand = models.CharField(max_length=80, verbose_name=_("Марка"))
    model = models.CharField(max_length=120, verbose_name=_("Модель"))
    year = models.PositiveIntegerField(verbose_name=_("Год выпуска"))
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Цена"))
    mileage_km = models.PositiveIntegerField(default=0, verbose_name=_("Пробег (км)"))
    fuel_type = models.CharField(max_length=40, blank=True, verbose_name=_("Топливо"))
    transmission = models.CharField(max_length=40, blank=True, verbose_name=_("Коробка"))
    color = models.CharField(max_length=40, blank=True, verbose_name=_("Цвет"))
    image_url = models.URLField(blank=True, verbose_name=_("Изображение (URL)"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Машина")
        verbose_name_plural = _("Машины")

    def __str__(self) -> str:
        return f"{self.brand} {self.model} ({self.year})"

    @property
    def gallery_image_urls(self):
        try:
            prefetched_images = getattr(self, "_prefetched_objects_cache", {}).get("images")
            image_items = list(prefetched_images) if prefetched_images is not None else list(self.images.order_by("order", "id"))
            if image_items:
                return [item.image_url for item in image_items if item.image]
        except (OperationalError, ProgrammingError):
            pass

        from .templatetags.car_image_filters import car_image_urls

        return car_image_urls(self.image_url, 30)


class CarCharacteristicGroup(models.Model):
    name = models.CharField(max_length=120, verbose_name=_("Группа характеристик"))
    slug = models.SlugField(max_length=150, unique=True)
    order = models.PositiveIntegerField(default=0, verbose_name=_("Порядок отображения"))

    class Meta:
        verbose_name = _("Группа характеристик")
        verbose_name_plural = _("Группы характеристик")
        ordering = ("order", "name")

    def __str__(self) -> str:
        return self.name


class CarCharacteristic(models.Model):
    class ValueType(models.TextChoices):
        INT = "int", _("Целое")
        DECIMAL = "decimal", _("Дробное")
        BOOL = "bool", _("Да/Нет")
        TEXT = "text", _("Текст")
        ENUM = "enum", _("Перечень")

    group = models.ForeignKey(
        CarCharacteristicGroup,
        on_delete=models.CASCADE,
        related_name="characteristics",
        verbose_name=_("Группа"),
    )
    name = models.CharField(max_length=180, verbose_name=_("Название характеристики"))
    slug = models.SlugField(max_length=200, unique=True)
    value_type = models.CharField(max_length=20, choices=ValueType.choices, default=ValueType.TEXT)
    unit = models.CharField(max_length=40, blank=True, verbose_name=_("Единицы измерения"))
    enum_options = models.TextField(
        blank=True,
        verbose_name=_("Варианты (для ENUM, через запятую)"),
        help_text=_("Пример: 4WD, AWD, FWD, RWD"),
    )

    class Meta:
        verbose_name = _("Характеристика")
        verbose_name_plural = _("Характеристики")
        ordering = ("group__order", "name")

    def __str__(self) -> str:
        return f"{self.group.name}: {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)


class CarCharacteristicValue(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="spec_values", verbose_name=_("Машина"))
    characteristic = models.ForeignKey(
        CarCharacteristic,
        on_delete=models.CASCADE,
        related_name="values",
        verbose_name=_("Характеристика"),
    )

    value_int = models.IntegerField(null=True, blank=True, verbose_name=_("Значение (int)"))
    value_decimal = models.DecimalField(
        null=True, blank=True, max_digits=14, decimal_places=3, verbose_name=_("Значение (decimal)")
    )
    value_bool = models.BooleanField(null=True, blank=True, verbose_name=_("Значение (bool)"))
    value_text = models.TextField(blank=True, verbose_name=_("Значение (text)"))
    value_enum = models.CharField(max_length=200, blank=True, verbose_name=_("Значение (enum)"))

    class Meta:
        verbose_name = _("Значение характеристики")
        verbose_name_plural = _("Значения характеристик")
        constraints = [
            models.UniqueConstraint(fields=("car", "characteristic"), name="unique_car_characteristic_value")
        ]

    def clean(self):
        filled = [
            self.value_int is not None,
            self.value_decimal is not None,
            self.value_bool is not None,
            bool(self.value_text.strip()) if isinstance(self.value_text, str) else bool(self.value_text),
            bool(self.value_enum.strip()) if isinstance(self.value_enum, str) else bool(self.value_enum),
        ]
        if sum(1 for value in filled if value) > 1:
            raise ValidationError(_("Заполнено несколько полей значения."))

    @property
    def value_display(self) -> str:
        current_type = self.characteristic.value_type
        if current_type == CarCharacteristic.ValueType.INT and self.value_int is not None:
            return str(self.value_int)
        if current_type == CarCharacteristic.ValueType.DECIMAL and self.value_decimal is not None:
            return str(self.value_decimal)
        if current_type == CarCharacteristic.ValueType.BOOL and self.value_bool is not None:
            return _("Да") if self.value_bool else _("Нет")
        if current_type == CarCharacteristic.ValueType.ENUM and self.value_enum:
            return self.value_enum
        if current_type == CarCharacteristic.ValueType.TEXT and self.value_text:
            return self.value_text

        if self.value_enum:
            return self.value_enum
        if self.value_text:
            return self.value_text
        if self.value_int is not None:
            return str(self.value_int)
        if self.value_decimal is not None:
            return str(self.value_decimal)
        if self.value_bool is not None:
            return _("Да") if self.value_bool else _("Нет")
        return "—"

    def __str__(self) -> str:
        return f"{self.car}: {self.characteristic}={self.value_display}"
