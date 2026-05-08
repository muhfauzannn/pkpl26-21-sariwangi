from django.contrib import admin

from .models import Voter


@admin.register(Voter)
class VoterAdmin(admin.ModelAdmin):
    list_display = ("full_name", "nik", "npm", "email", "faculty", "status", "has_voted")
    list_filter = ("status", "has_voted", "faculty")
    search_fields = ("full_name", "nik", "npm", "email")
    readonly_fields = ("created_at", "updated_at")
