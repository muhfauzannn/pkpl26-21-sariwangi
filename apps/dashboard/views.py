from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from apps.candidates.models import Candidate
from apps.voting.models import Vote

from .models import AuditLog


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_votes"] = Vote.objects.count()
        context["total_candidates"] = Candidate.objects.filter(
            status=Candidate.Status.APPROVED,
        ).count()
        context["results"] = [
            {
                "candidate": c,
                "vote_count": c.votes.count(),
            }
            for c in Candidate.objects.filter(
                status=Candidate.Status.APPROVED,
            ).order_by("candidate_number")
        ]
        context["pending_candidates"] = Candidate.objects.filter(
            status=Candidate.Status.PENDING,
        ).count()
        context["recent_logs"] = AuditLog.objects.all()[:20]
        return context


class AuditLogListView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/audit_log.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["logs"] = AuditLog.objects.all()[:100]
        return context
