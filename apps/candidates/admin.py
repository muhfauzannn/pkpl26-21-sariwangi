from django.contrib import admin

from .models import Candidate, CandidateMember


class CandidateMemberInline(admin.TabularInline):
    model = CandidateMember
    extra = 1


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ("name", "candidate_number", "status", "verified_by", "created_at")
    list_filter = ("status",)
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [CandidateMemberInline]
