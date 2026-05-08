from django.contrib import admin

from .models import Vote


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ("voter", "candidate", "voted_at")
    list_filter = ("voted_at",)
    readonly_fields = ("voter", "candidate", "voted_at")
