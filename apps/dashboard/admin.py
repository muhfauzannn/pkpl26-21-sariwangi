from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action", "description", "ip_address", "timestamp")
    list_filter = ("action", "timestamp")
    search_fields = ("description", "user__username")
    readonly_fields = ("user", "action", "description", "ip_address", "timestamp")
