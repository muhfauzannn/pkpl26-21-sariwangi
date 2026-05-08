from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from apps.candidates.models import Candidate
from apps.voters.models import Voter
from apps.voting.models import Vote

from .models import AuditLog


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_votes = Vote.objects.count()
        total_candidates = Candidate.objects.filter(
            status=Candidate.Status.APPROVED,
        ).count()
        total_voters = Voter.objects.filter(status=Voter.Status.ACTIVE).count()
        voted_count = Voter.objects.filter(has_voted=True).count()

        context["total_votes"] = total_votes
        context["total_candidates"] = total_candidates
        context["pending_candidates"] = Candidate.objects.filter(
            status=Candidate.Status.PENDING,
        ).count()
        context["total_voters"] = total_voters
        context["voted_count"] = voted_count
        context["remaining_voters"] = total_voters - voted_count
        context["results"] = [
            {
                "candidate": c,
                "vote_count": c.votes.count(),
            }
            for c in Candidate.objects.filter(
                status=Candidate.Status.APPROVED,
            ).order_by("candidate_number")
        ]
        context["recent_logs"] = AuditLog.objects.all()[:8]
        return context


class AuditLogListView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/audit_log.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["logs"] = AuditLog.objects.all()[:100]
        return context
