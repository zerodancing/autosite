from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


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
    text = models.TextField(verbose_name=_("Сообщение"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Время отправки"))

    class Meta:
        verbose_name = _("Сообщение")
        verbose_name_plural = _("Сообщения")
        ordering = ("created_at",)

    def __str__(self) -> str:
        return f"{self.sender}: {self.text[:30]}"
