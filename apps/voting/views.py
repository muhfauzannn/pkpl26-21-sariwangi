from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.shortcuts import redirect
from django.views.generic import FormView, TemplateView

from candidates.models import Candidate

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
            messages.success(self.request, "Voting berhasil dicatat.")
            return redirect("voting:success")
        except IntegrityError:
            messages.error(self.request, "Anda sudah melakukan voting sebelumnya.")
            return redirect("voting:results")


class VoteSuccessView(LoginRequiredMixin, TemplateView):
    template_name = "voting/vote_success.html"


class VotingResultsView(TemplateView):
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
