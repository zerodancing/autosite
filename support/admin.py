from django.contrib import admin

from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    fields = ("sender", "text", "created_at")
    readonly_fields = ("created_at",)
    extra = 0


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "client", "assigned_operator", "updated_at")
    list_filter = ("updated_at",)
    search_fields = ("subject", "client__username", "assigned_operator__username")
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "sender", "created_at")
    search_fields = ("text", "sender__username")
