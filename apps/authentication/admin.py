from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import LoginAttempt, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "is_active", "is_staff")
    list_filter = ("role", "is_active", "is_staff")
    fieldsets = UserAdmin.fieldsets + (
        ("Role", {"fields": ("role",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Role", {"fields": ("role",)}),
    )


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "ip_address", "timestamp", "success")
    list_filter = ("success", "timestamp")
    readonly_fields = ("user", "ip_address", "timestamp", "success")
