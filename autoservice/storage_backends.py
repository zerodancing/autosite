from pathlib import Path

from cloudinary import api, uploader
from cloudinary.utils import cloudinary_url
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class CloudinaryMediaStorage(Storage):
    """Minimal storage backend for image media hosted in Cloudinary."""

    def _normalize_name(self, name: str) -> str:
        return str(name).replace("\\", "/").lstrip("/")

    def _split_name(self, name: str) -> tuple[str, str]:
        normalized = self._normalize_name(name)
        path = Path(normalized)
        extension = path.suffix.lstrip(".").lower()
        public_id = path.with_suffix("").as_posix()
        return public_id, extension

    def _open(self, name, mode="rb"):
        raise NotImplementedError("CloudinaryMediaStorage does not support opening files.")

    def _save(self, name, content):
        normalized = self._normalize_name(name)
        public_id, extension = self._split_name(normalized)

        if hasattr(content, "open"):
            content.open("rb")

        upload_options = {
            "public_id": public_id,
            "resource_type": "image",
            "overwrite": True,
            "invalidate": True,
            "unique_filename": False,
            "use_filename": False,
        }
        if extension:
            upload_options["format"] = extension

        result = uploader.upload(content, **upload_options)
        stored_public_id = result.get("public_id", public_id)
        stored_format = (result.get("format") or extension).lower() if (result.get("format") or extension) else ""
        return f"{stored_public_id}.{stored_format}" if stored_format else stored_public_id

    def delete(self, name):
        public_id, _ = self._split_name(name)
        uploader.destroy(public_id, resource_type="image", invalidate=True)

    def exists(self, name):
        public_id, _ = self._split_name(name)
        try:
            api.resource(public_id, resource_type="image", type="upload")
            return True
        except Exception:
            return False

    def url(self, name):
        source = str(name).strip()
        if source.startswith(("http://", "https://")):
            return source

        public_id, extension = self._split_name(source)
        url, _ = cloudinary_url(
            public_id,
            resource_type="image",
            type="upload",
            secure=True,
            format=extension or None,
        )
        return url

    def listdir(self, path):
        return [], []

    def size(self, name):
        public_id, _ = self._split_name(name)
        try:
            resource = api.resource(public_id, resource_type="image", type="upload")
        except Exception:
            return 0
        return int(resource.get("bytes") or 0)
