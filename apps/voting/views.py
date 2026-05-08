from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.shortcuts import redirect
from django.views.generic import FormView, TemplateView

from apps.candidates.models import Candidate
from apps.dashboard.services import log_action
from apps.voters.models import Voter

from .forms import VoteForm
from .models import Vote


class VotingView(LoginRequiredMixin, FormView):
    template_name = "voting/vote.html"
    form_class = VoteForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "pemilih":
            messages.error(request, "Hanya pemilih yang bisa melakukan voting.")
            return redirect("/")

        if Vote.objects.filter(voter=request.user).exists():
            messages.warning(request, "Anda sudah melakukan voting.")
            return redirect("voting:results")

        voter = Voter.objects.filter(user=request.user).first()
        if not voter:
            messages.error(request, "Data pemilih Anda tidak ditemukan. Hubungi pengawas.")
            return redirect("voting:results")

        if voter.status != Voter.Status.ACTIVE:
            messages.error(request, "Status pemilih Anda tidak aktif. Hubungi pengawas.")
            return redirect("voting:results")

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["candidates"] = Candidate.objects.filter(
            status=Candidate.Status.APPROVED,
        ).order_by("candidate_number")
        return context

    def form_valid(self, form):
        try:
            Vote.objects.create(
                voter=self.request.user,
                candidate=form.cleaned_data["candidate"],
            )

            voter = Voter.objects.filter(user=self.request.user).first()
            if voter:
                voter.has_voted = True
                voter.save(update_fields=["has_voted"])

            messages.success(self.request, "Voting berhasil dicatat.")
            log_action(self.request, "vote", f"User \"{self.request.user.username}\" memilih paslon \"{form.cleaned_data['candidate'].name}\"")
            return redirect("voting:success")
        except IntegrityError:
            messages.error(self.request, "Anda sudah melakukan voting sebelumnya.")
            return redirect("voting:results")


class VoteSuccessView(LoginRequiredMixin, TemplateView):
    template_name = "voting/vote_success.html"


class VotingResultsView(LoginRequiredMixin, TemplateView):
    template_name = "voting/results.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["results"] = [
            {
                "candidate": c,
                "vote_count": c.votes.count(),
            }
            for c in Candidate.objects.filter(
                status=Candidate.Status.APPROVED,
            ).order_by("candidate_number")
        ]
        context["total_votes"] = Vote.objects.count()
        return context
