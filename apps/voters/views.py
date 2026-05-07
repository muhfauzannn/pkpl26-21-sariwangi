from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

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
        messages.success(self.request, f"Data pemilih \"{form.cleaned_data['full_name']}\" berhasil ditambahkan.")
        return super().form_valid(form)


class VoterUpdateView(LoginRequiredMixin, UpdateView):
    model = Voter
    form_class = VoterForm
    template_name = "voters/voter_form.html"
    success_url = reverse_lazy("voters:list")

    def form_valid(self, form):
        messages.success(self.request, f"Data pemilih \"{form.cleaned_data['full_name']}\" berhasil diperbarui.")
        return super().form_valid(form)


class VoterDeleteView(LoginRequiredMixin, DeleteView):
    model = Voter
    template_name = "voters/voter_confirm_delete.html"
    success_url = reverse_lazy("voters:list")

    def form_valid(self, form):
        name = self.object.full_name
        messages.success(self.request, f"Data pemilih \"{name}\" berhasil dihapus.")
        return super().form_valid(form)
