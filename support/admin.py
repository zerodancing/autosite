from django.contrib import admin
from django.utils.html import format_html

from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    fields = ("sender", "text", "image_preview", "voice_preview", "created_at")
    readonly_fields = ("image_preview", "voice_preview", "created_at")
    extra = 0

    @admin.display(description="Фото")
    def image_preview(self, obj):
        if not obj or not obj.image:
            return "—"
        return format_html('<a href="{}" target="_blank" rel="noopener">Открыть фото</a>', obj.image_url)

    @admin.display(description="Голос")
    def voice_preview(self, obj):
        if not obj or not obj.voice_message:
            return "—"
        return format_html('<audio controls preload="none" src="{}"></audio>', obj.voice_message_url)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "client", "assigned_operator", "updated_at")
    list_filter = ("updated_at",)
    search_fields = ("subject", "client__username", "assigned_operator__username")
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "sender", "has_image", "has_voice", "created_at")
    search_fields = ("text", "sender__username")
    readonly_fields = ("image_preview", "voice_preview", "created_at")
    fields = ("conversation", "sender", "text", "image", "image_preview", "voice_message", "voice_preview", "created_at")

    @admin.display(boolean=True, description="Фото")
    def has_image(self, obj):
        return bool(obj.image)

    @admin.display(boolean=True, description="Голос")
    def has_voice(self, obj):
        return bool(obj.voice_message)

    @admin.display(description="Фото")
    def image_preview(self, obj):
        if not obj or not obj.image:
            return "—"
        return format_html('<a href="{}" target="_blank" rel="noopener">Открыть фото</a>', obj.image_url)

    @admin.display(description="Голос")
    def voice_preview(self, obj):
        if not obj or not obj.voice_message:
            return "—"
        return format_html('<audio controls preload="none" src="{}"></audio>', obj.voice_message_url)
