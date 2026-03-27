import os
from urllib.parse import urlparse

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

from .settings import *  # noqa: F401,F403


LOCAL_ALLOWED_HOSTS = {"127.0.0.1", "localhost"}


def _csv_env(name: str) -> list[str]:
    return [item.strip() for item in os.environ.get(name, "").split(",") if item.strip()]


def _append_unique(target: list[str], value: str) -> None:
    if value and value not in target:
        target.append(value)


def _hostname_from_value(value: str) -> str:
    if not value:
        return ""
    candidate = value.strip()
    if not candidate:
        return ""
    if candidate == "*":
        return "*"
    if "://" not in candidate:
        candidate = f"https://{candidate}"
    parsed = urlparse(candidate)
    return (parsed.hostname or parsed.netloc).strip()


def _normalize_origin(value: str) -> str:
    if not value:
        return ""
    candidate = value.strip()
    if not candidate:
        return ""
    if "://" not in candidate:
        candidate = f"https://{candidate.lstrip('/')}"
    parsed = urlparse(candidate)
    if not parsed.netloc:
        return ""
    return f"{parsed.scheme or 'https'}://{parsed.netloc}"


DEBUG = False

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured(
        "Production requires DJANGO_SECRET_KEY (or SECRET_KEY) in the environment."
    )

if "storages" not in INSTALLED_APPS:
    INSTALLED_APPS = [*INSTALLED_APPS, "storages"]

MIDDLEWARE = list(MIDDLEWARE)
white_noise_middleware = "whitenoise.middleware.WhiteNoiseMiddleware"
security_middleware = "django.middleware.security.SecurityMiddleware"
if white_noise_middleware not in MIDDLEWARE:
    security_index = MIDDLEWARE.index(security_middleware)
    MIDDLEWARE.insert(security_index + 1, white_noise_middleware)

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

cloudinary_cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME", "").strip()
cloudinary_api_key = os.environ.get("CLOUDINARY_API_KEY", "").strip()
cloudinary_api_secret = os.environ.get("CLOUDINARY_API_SECRET", "").strip()
use_cloudinary_media = all(
    [cloudinary_cloud_name, cloudinary_api_key, cloudinary_api_secret]
)

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

if use_cloudinary_media:
    import cloudinary

    cloudinary.config(
        cloud_name=cloudinary_cloud_name,
        api_key=cloudinary_api_key,
        api_secret=cloudinary_api_secret,
        secure=True,
    )
    STORAGES["default"] = {
        "BACKEND": "autoservice.storage_backends.CloudinaryMediaStorage",
    }
    MEDIA_URL = os.environ.get("DJANGO_MEDIA_URL", "").strip()
    if not MEDIA_URL:
        MEDIA_URL = f"https://res.cloudinary.com/{cloudinary_cloud_name}/image/upload/"
    MEDIA_URL = MEDIA_URL.rstrip("/") + "/"
else:
    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "access_key": os.environ.get("AWS_ACCESS_KEY_ID", "").strip(),
            "secret_key": os.environ.get("AWS_SECRET_ACCESS_KEY", "").strip(),
            "bucket_name": os.environ.get("AWS_STORAGE_BUCKET_NAME", "").strip(),
            "region_name": os.environ.get("AWS_S3_REGION_NAME", "").strip() or None,
            "endpoint_url": os.environ.get("AWS_S3_ENDPOINT_URL", "").strip(),
            "custom_domain": os.environ.get("AWS_S3_CUSTOM_DOMAIN", "").strip() or None,
            "default_acl": None,
            "querystring_auth": False,
            "file_overwrite": False,
            "object_parameters": {
                "CacheControl": "max-age=86400",
            },
        },
    }

    required_storage_values = {
        "AWS_STORAGE_BUCKET_NAME": STORAGES["default"]["OPTIONS"]["bucket_name"],
        "AWS_S3_ENDPOINT_URL": STORAGES["default"]["OPTIONS"]["endpoint_url"],
        "AWS_ACCESS_KEY_ID": STORAGES["default"]["OPTIONS"]["access_key"],
        "AWS_SECRET_ACCESS_KEY": STORAGES["default"]["OPTIONS"]["secret_key"],
    }
    missing_storage_values = [
        name for name, value in required_storage_values.items() if not value
    ]
    if missing_storage_values:
        raise ImproperlyConfigured(
            "Production media storage is not configured. "
            "Set Cloudinary credentials or S3-compatible storage variables. Missing: "
            + ", ".join(sorted(missing_storage_values))
        )

    MEDIA_URL = os.environ.get("DJANGO_MEDIA_URL", "").strip()
    custom_media_domain = STORAGES["default"]["OPTIONS"]["custom_domain"]
    if not MEDIA_URL and custom_media_domain:
        MEDIA_URL = f"https://{custom_media_domain.rstrip('/')}/"
    if MEDIA_URL:
        MEDIA_URL = MEDIA_URL.rstrip("/") + "/"
    else:
        raise ImproperlyConfigured(
            "Set DJANGO_MEDIA_URL or AWS_S3_CUSTOM_DOMAIN for public media URLs."
        )

allowed_hosts = list(ALLOWED_HOSTS)
for value in _csv_env("DJANGO_ALLOWED_HOSTS"):
    _append_unique(allowed_hosts, _hostname_from_value(value))
_append_unique(allowed_hosts, "127.0.0.1")
_append_unique(allowed_hosts, "localhost")
_append_unique(
    allowed_hosts,
    _hostname_from_value(os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()),
)
_append_unique(
    allowed_hosts,
    _hostname_from_value(os.environ.get("DJANGO_SITE_URL", "").strip()),
)
ALLOWED_HOSTS = allowed_hosts
public_allowed_hosts = [host for host in ALLOWED_HOSTS if host not in LOCAL_ALLOWED_HOSTS]
if not public_allowed_hosts:
    raise ImproperlyConfigured(
        "Set DJANGO_ALLOWED_HOSTS, DJANGO_SITE_URL, or RENDER_EXTERNAL_HOSTNAME for production."
    )

csrf_trusted_origins = []
for value in _csv_env("DJANGO_CSRF_TRUSTED_ORIGINS"):
    _append_unique(csrf_trusted_origins, _normalize_origin(value))
_append_unique(
    csrf_trusted_origins,
    _normalize_origin(os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()),
)
_append_unique(
    csrf_trusted_origins,
    _normalize_origin(os.environ.get("DJANGO_SITE_URL", "").strip()),
)
CSRF_TRUSTED_ORIGINS = csrf_trusted_origins
if not CSRF_TRUSTED_ORIGINS:
    raise ImproperlyConfigured(
        "Set DJANGO_CSRF_TRUSTED_ORIGINS, DJANGO_SITE_URL, or RENDER_EXTERNAL_HOSTNAME for production."
    )

database_url = os.environ.get("DATABASE_URL", "").strip()
database_conn_max_age = int(os.environ.get("DJANGO_DB_CONN_MAX_AGE", "600"))
if database_url:
    DATABASES["default"] = dj_database_url.parse(
        database_url,
        conn_max_age=database_conn_max_age,
        conn_health_checks=True,
    )
else:
    DATABASES["default"]["CONN_MAX_AGE"] = database_conn_max_age
    DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
    if DATABASES["default"]["ENGINE"].endswith("sqlite3"):
        raise ImproperlyConfigured(
            "Production requires DATABASE_URL or POSTGRES_* environment variables."
        )

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SECURE_SSL_REDIRECT = os.environ.get("DJANGO_SECURE_SSL_REDIRECT", "1") == "1"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "3600"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = (
    os.environ.get("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", "1") == "1"
)
SECURE_HSTS_PRELOAD = os.environ.get("DJANGO_SECURE_HSTS_PRELOAD", "0") == "1"
SECURE_REFERRER_POLICY = "same-origin"
