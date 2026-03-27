from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser

admin.site.site_header = "Админ-панель автосервиса"
admin.site.site_title = "Автосервис"
admin.site.index_title = "Управление сайтом"


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ("username", "email", "full_name", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("username", "email", "full_name")

    fieldsets = UserAdmin.fieldsets + (
        (
            "Данные пользователя",
            {"fields": ("role", "full_name", "phone")},
        ),
    )
