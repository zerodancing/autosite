from pathlib import Path

from django import forms
from django.core.files.storage import default_storage
from django.db.utils import OperationalError, ProgrammingError
from django.template.defaultfilters import slugify
from django.utils import timezone

from .models import Car, CarImage, Service
from .widgets import AdminDropzoneFileInput, AdminDropzoneMultipleFileInput


class MultipleImageField(forms.FileField):
    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(item, initial) for item in data]
        if not data:
            return []
        return [single_file_clean(data, initial)]


def _safe_slug(*parts: object, fallback: str) -> str:
    values = [slugify(str(part)) for part in parts if part]
    values = [value for value in values if value]
    return "-".join(values) or fallback


def _file_extension(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    return ext if ext else ".jpg"


def _media_storage():
    return default_storage


def save_service_image(service: Service, uploaded_file) -> str:
    storage = _media_storage()
    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    stem = _safe_slug(service.title, fallback="service")
    relative_path = f"services/{stem}-{timestamp}{_file_extension(uploaded_file.name)}"

    if storage.exists(relative_path):
        storage.delete(relative_path)
    return storage.save(relative_path, uploaded_file)


def save_car_gallery(car: Car, uploaded_files: list) -> str:
    storage = _media_storage()
    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    folder = _safe_slug(car.brand, fallback="cars")
    stem = _safe_slug(car.brand, car.model, car.year, fallback="car")
    base_name = f"{stem}-{timestamp}"

    try:
        next_order = (car.images.order_by("-order").values_list("order", flat=True).first() or 0) + 1
    except (OperationalError, ProgrammingError):
        next_order = 1

    first_relative_path = car.image_url or ""
    for offset, uploaded_file in enumerate(uploaded_files):
        index = next_order + offset
        relative_path = f"{folder}/{base_name}-{index}{_file_extension(uploaded_file.name)}"
        if storage.exists(relative_path):
            storage.delete(relative_path)
        saved_path = storage.save(relative_path, uploaded_file)
        try:
            CarImage.objects.create(
                car=car,
                image=saved_path,
                order=index,
                alt_text=f"{car.brand} {car.model}",
            )
        except (OperationalError, ProgrammingError):
            pass
        if not first_relative_path:
            first_relative_path = saved_path
    return first_relative_path


class ServiceAdminForm(forms.ModelForm):
    image_url = forms.CharField(
        required=False,
        label="Ссылка или путь к изображению",
        help_text="Можно вставить внешний URL или оставить поле пустым и загрузить файл ниже.",
        widget=forms.TextInput(
            attrs={
                "placeholder": "https://... или services/my-service.webp",
            }
        ),
    )
    image_upload = forms.FileField(
        required=False,
        label="Загрузить изображение",
        help_text="Перетащите картинку сюда или нажмите, чтобы выбрать файл.",
        widget=AdminDropzoneFileInput(
            attrs={
                "class": "admin-dropzone__input",
                "accept": "image/*",
                "dropzone_title": "Перетащите обложку услуги сюда",
                "dropzone_hint": "или нажмите, чтобы выбрать файл",
            }
        ),
    )

    class Meta:
        model = Service
        fields = "__all__"


class CarAdminForm(forms.ModelForm):
    gallery_uploads = MultipleImageField(
        required=False,
        label="Галерея изображений",
        help_text="Можно перетаскивать по одной или по несколько фотографий подряд. До сохранения они будут накапливаться, после сохранения попадут в общую галерею.",
        widget=AdminDropzoneMultipleFileInput(
            attrs={
                "class": "admin-dropzone__input",
                "accept": "image/*",
                "dropzone_title": "Перетащите сюда всю галерею",
                "dropzone_hint": "можно добавлять фото по одной, партиями и повторно до сохранения",
            }
        ),
    )

    class Meta:
        model = Car
        exclude = ("image_url",)
