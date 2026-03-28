from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from catalog.utils import resolve_uploaded_media_url


class Conversation(models.Model):
    """
    Чат поддержки. Для курсовой делаем упрощенную модель:
    - `client` — кто создал обращение
    - `assigned_operator` — кому назначен чат (если сотрудник ответил/взял в работу)
    """

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="support_conversations",
        verbose_name=_("Клиент"),
    )
    assigned_operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="operator_conversations",
        verbose_name=_("Оператор"),
    )
    subject = models.CharField(max_length=200, blank=True, default="", verbose_name=_("Тема"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Создано"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Обновлено"))

    class Meta:
        verbose_name = _("Диалог")
        verbose_name_plural = _("Диалоги")
        ordering = ("-updated_at",)

    def __str__(self) -> str:
        return self.subject or f"Диалог #{self.pk}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField(blank=True, default="", verbose_name=_("Сообщение"))
    image = models.FileField(
        upload_to="support/images/%Y/%m/",
        blank=True,
        verbose_name=_("Изображение"),
    )
    voice_message = models.FileField(
        upload_to="support/voice/%Y/%m/",
        blank=True,
        verbose_name=_("Голосовое сообщение"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Время отправки"))

    class Meta:
        verbose_name = _("Сообщение")
        verbose_name_plural = _("Сообщения")
        ordering = ("created_at",)

    def clean(self):
        text = (self.text or "").strip()
        if not text and not self.image and not self.voice_message:
            raise ValidationError(_("Сообщение должно содержать текст, изображение или голосовое вложение."))

    @property
    def image_url(self) -> str:
        if not self.image:
            return ""
        try:
            return self.image.url
        except Exception:
            return resolve_uploaded_media_url(self.image.name)

    @property
    def voice_message_url(self) -> str:
        if not self.voice_message:
            return ""
        try:
            return self.voice_message.url
        except Exception:
            return resolve_uploaded_media_url(self.voice_message.name)

    @property
    def voice_message_mime_type(self) -> str:
        mapping = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "ogg": "audio/ogg",
            "oga": "audio/ogg",
            "opus": "audio/ogg",
            "m4a": "audio/mp4",
            "aac": "audio/aac",
            "mp4": "audio/mp4",
            "webm": "audio/webm",
        }
        extension = (self.voice_message.name.rsplit(".", 1)[-1].lower() if self.voice_message else "")
        return mapping.get(extension, "audio/mpeg")

    @property
    def voice_message_browser_url(self) -> str:
        if not self.voice_message:
            return ""

        extension = self.voice_message.name.rsplit(".", 1)[-1].lower() if "." in self.voice_message.name else ""
        original_url = self.voice_message_url
        if extension in {"mp3", "wav", "ogg", "oga", "m4a", "aac", "mp4"}:
            return original_url

        storage = getattr(self.voice_message, "storage", None)
        if storage and storage.__class__.__name__ == "CloudinaryMediaStorage":
            try:
                from cloudinary.utils import cloudinary_url
                from pathlib import Path

                public_id = Path(str(self.voice_message.name).replace("\\", "/").lstrip("/")).with_suffix("").as_posix()
                transcoded_url, _options = cloudinary_url(
                    public_id,
                    resource_type="video",
                    type="upload",
                    secure=True,
                    format="mp3",
                )
                return transcoded_url
            except Exception:
                return original_url

        return original_url

    @property
    def preview_text(self) -> str:
        text = (self.text or "").strip()
        if text:
            return text
        if self.image and self.voice_message:
            return "Фото и голосовое сообщение"
        if self.image:
            return "Фото"
        if self.voice_message:
            return "Голосовое сообщение"
        return "Сообщение"

    def __str__(self) -> str:
        return f"{self.sender}: {self.preview_text[:30]}"
