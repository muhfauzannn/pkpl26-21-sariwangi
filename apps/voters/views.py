from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from apps.dashboard.services import log_action

from .forms import VoterForm
from .models import Voter


class VoterListView(LoginRequiredMixin, ListView):
    model = Voter
    template_name = "voters/voter_list.html"
    context_object_name = "voters"
    ordering = ["-created_at"]


class VoterCreateView(LoginRequiredMixin, CreateView):
    model = Voter
    form_class = VoterForm
    template_name = "voters/voter_form.html"
    success_url = reverse_lazy("voters:list")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Data pemilih \"{self.object.full_name}\" berhasil ditambahkan.")
        log_action(self.request, "voter_create", f"Menambahkan pemilih \"{self.object.full_name}\" (NIK: {self.object.nik})")
        return response


class VoterUpdateView(LoginRequiredMixin, UpdateView):
    model = Voter
    form_class = VoterForm
    template_name = "voters/voter_form.html"
    success_url = reverse_lazy("voters:list")

    def form_valid(self, form):
        messages.success(self.request, f"Data pemilih \"{form.cleaned_data['full_name']}\" berhasil diperbarui.")
        log_action(self.request, "voter_update", f"Memperbarui pemilih \"{form.cleaned_data['full_name']}\"")
        return super().form_valid(form)


class VoterDeleteView(LoginRequiredMixin, DeleteView):
    model = Voter
    template_name = "voters/voter_confirm_delete.html"
    success_url = reverse_lazy("voters:list")

    def form_valid(self, form):
        name = self.object.full_name
        messages.success(self.request, f"Data pemilih \"{name}\" berhasil dihapus.")
        log_action(self.request, "voter_delete", f"Menghapus pemilih \"{name}\"")
        return super().form_valid(form)
