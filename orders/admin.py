from django.contrib import admin

from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "order_type", "status", "total_price", "scheduled_at", "created_at")
    list_filter = ("order_type", "status", "created_at")
    search_fields = ("user__username", "customer_comment")
    readonly_fields = ("created_at",)
