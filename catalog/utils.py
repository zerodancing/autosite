from django.conf import settings
from django.core.files.storage import default_storage


def resolve_uploaded_media_url(value: str) -> str:
    if not value:
        return ""

    source = str(value).strip()
    if not source:
        return ""
    if source.startswith(("http://", "https://", "/")):
        return source

    normalized = source.replace("\\", "/").lstrip("/")

    try:
        return default_storage.url(normalized)
    except Exception:
        media_url = (settings.MEDIA_URL or "").rstrip("/")
        return f"{media_url}/{normalized}"
