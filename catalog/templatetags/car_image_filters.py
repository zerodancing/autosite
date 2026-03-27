import re

from django import template
from django.core.files.storage import default_storage

from catalog.utils import resolve_uploaded_media_url

register = template.Library()


@register.filter(name="car_image_urls")
def car_image_urls(image_url: str, max_images: int = 5):
    if not image_url:
        return []

    source = str(image_url).strip()
    max_images = int(max_images) if str(max_images).isdigit() else 5

    if source.startswith(("http://", "https://")):
        return [source]

    normalized = source.replace("\\", "/")
    match = re.match(r"^(?P<prefix>.*?)(?P<num>\d+)\.(?P<ext>[a-zA-Z0-9]+)$", normalized)
    if not match:
        return [resolve_uploaded_media_url(normalized)]

    prefix = match.group("prefix")
    ext = match.group("ext")

    urls = []
    for index in range(1, max_images + 1):
        relative_path = f"{prefix}{index}.{ext}".lstrip("/")
        if not default_storage.exists(relative_path):
            if index == 1:
                urls.append(resolve_uploaded_media_url(relative_path))
            break
        urls.append(resolve_uploaded_media_url(relative_path))
    return urls
