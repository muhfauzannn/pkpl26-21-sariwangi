from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView

from apps.dashboard.services import log_action

from .forms import CandidateMemberFormSet, CandidateRegistrationForm
from .models import Candidate


class CandidateListView(LoginRequiredMixin, ListView):
    model = Candidate
    template_name = "candidates/candidate_list.html"
    context_object_name = "candidates"

    def get_queryset(self):
        qs = Candidate.objects.all()
        if self.request.user.role == "paslon":
            qs = qs.filter(user=self.request.user)
        elif self.request.user.role == "pemilih":
            qs = qs.filter(status=Candidate.Status.APPROVED)
        return qs


class CandidateDetailView(LoginRequiredMixin, DetailView):
    model = Candidate
    template_name = "candidates/candidate_detail.html"
    context_object_name = "candidate"

    def get_queryset(self):
        qs = Candidate.objects.all()
        if self.request.user.role == "paslon":
            return qs.filter(user=self.request.user)
        if self.request.user.role == "pemilih":
            return qs.filter(status=Candidate.Status.APPROVED)
        return qs


class CandidateRegisterView(LoginRequiredMixin, CreateView):
    model = Candidate
    form_class = CandidateRegistrationForm
    template_name = "candidates/candidate_register.html"
    success_url = reverse_lazy("candidates:list")

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != "paslon":
            raise PermissionDenied("Hanya paslon yang bisa mendaftar.")
        if Candidate.objects.filter(user=request.user).exists():
            messages.warning(request, "Anda sudah terdaftar sebagai paslon.")
            return redirect("candidates:list")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.method == "POST":
            context["member_formset"] = CandidateMemberFormSet(
                self.request.POST, self.request.FILES,
            )
        else:
            context["member_formset"] = CandidateMemberFormSet()
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        context = self.get_context_data()
        member_formset = context["member_formset"]
        if member_formset.is_valid():
            self.object = form.save()
            member_formset.instance = self.object
            member_formset.save()
            messages.success(self.request, "Pendaftaran paslon berhasil dikirim. Menunggu verifikasi pengawas.")
            log_action(self.request, "candidate_register", f"Paslon \"{self.object.name}\" mendaftar")
            return redirect(self.success_url)
        return self.form_invalid(form)


class CandidateApproveView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if request.user.role != "pengawas":
            raise PermissionDenied("Hanya pengawas yang bisa memverifikasi.")

        candidate = get_object_or_404(Candidate, pk=pk)
        if candidate.status != Candidate.Status.PENDING:
            messages.warning(request, "Paslon sudah diverifikasi sebelumnya.")
            return redirect("candidates:detail", pk=pk)

        max_number = (
            Candidate.objects.filter(candidate_number__isnull=False)
            .order_by("-candidate_number")
            .values_list("candidate_number", flat=True)
            .first()
        )
        candidate.candidate_number = (max_number or 0) + 1
        candidate.status = Candidate.Status.APPROVED
        candidate.verified_by = request.user
        candidate.save()
        messages.success(request, f"Paslon \"{candidate.name}\" berhasil disetujui (No. {candidate.candidate_number}).")
        log_action(request, "candidate_approve", f"Menyetujui paslon \"{candidate.name}\" (No. {candidate.candidate_number})")
        return redirect("candidates:detail", pk=pk)


class CandidateRejectView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if request.user.role != "pengawas":
            raise PermissionDenied("Hanya pengawas yang bisa memverifikasi.")

        candidate = get_object_or_404(Candidate, pk=pk)
        if candidate.status != Candidate.Status.PENDING:
            messages.warning(request, "Paslon sudah diverifikasi sebelumnya.")
            return redirect("candidates:detail", pk=pk)

        candidate.status = Candidate.Status.REJECTED
        candidate.verified_by = request.user
        candidate.save()
        messages.success(request, f"Paslon \"{candidate.name}\" ditolak.")
        log_action(request, "candidate_reject", f"Menolak paslon \"{candidate.name}\"")
        return redirect("candidates:detail", pk=pk)
