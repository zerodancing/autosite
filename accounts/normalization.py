import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


PHONE_DIGITS_RE = re.compile(r"\D+")


def normalize_email(value: str | None) -> str:
    return (value or "").strip().lower()


def normalize_phone(value: str | None, *, raise_on_error: bool = False) -> str:
    raw_value = (value or "").strip()
    if not raw_value:
        return ""

    digits = PHONE_DIGITS_RE.sub("", raw_value)

    if len(digits) == 10:
        return f"+7{digits}"
    if len(digits) == 11 and digits[0] in {"7", "8"}:
        return f"+7{digits[-10:]}"
    if 11 <= len(digits) <= 15:
        return f"+{digits}"

    if raise_on_error:
        raise ValidationError(
            _("Укажите номер телефона в формате +7XXXXXXXXXX или +XXXXXXXXXXX."),
            code="invalid_phone",
        )

    return raw_value
