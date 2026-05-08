from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import FormView

from apps.dashboard.services import log_action

from .forms import LoginForm, RegistrationForm
from .models import User
from .services import perform_login, perform_logout


class LoginView(FormView):
    template_name = "authentication/login.html"
    form_class = LoginForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self._get_role_url(request.user.role))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user, error = perform_login(
            self.request,
            form.cleaned_data["username"],
            form.cleaned_data["password"],
        )
        if error:
            form.add_error(None, error)
            return self.form_invalid(form)
        log_action(self.request, "login", f"User \"{user.username}\" berhasil login")
        return redirect(self._get_role_url(user.role))

    def _get_role_url(self, role):
        urls = {
            User.Role.PENGAWAS: "/dashboard/",
            User.Role.PASLON: "/candidates/",
            User.Role.PEMILIH: "/voting/",
        }
        return urls.get(role, "/dashboard/")


class LogoutView(View):
    def post(self, request):
        log_action(request, "logout", f"User \"{request.user.username}\" logout")
        perform_logout(request)
        return redirect(reverse("authentication:login"))


class RegisterView(FormView):
    template_name = "authentication/register.html"
    form_class = RegistrationForm
    success_url = "/auth/login/"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self._get_role_url(request.user.role))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = User.objects.create_user(
            username=form.cleaned_data["username"],
            email=form.cleaned_data["email"],
            password=form.cleaned_data["password1"],
            first_name=form.cleaned_data["first_name"],
            last_name=form.cleaned_data["last_name"],
            role=form.cleaned_data["role"],
        )
        user.is_active = True
        user.save()

        if form.cleaned_data["role"] == User.Role.PEMILIH:
            from apps.voters.models import Voter
            Voter.objects.create(
                user=user,
                nik=form.cleaned_data["nik"],
                npm=form.cleaned_data["npm"],
                email=form.cleaned_data["email"],
                full_name=f"{form.cleaned_data['first_name']} {form.cleaned_data['last_name']}".strip(),
                faculty=form.cleaned_data["faculty"],
                study_program=form.cleaned_data["study_program"],
                status=Voter.Status.ACTIVE,
            )

        messages.success(self.request, "Registrasi berhasil. Silakan login.")
        return super().form_valid(form)

    def _get_role_url(self, role):
        urls = {
            User.Role.PENGAWAS: "/dashboard/",
            User.Role.PASLON: "/candidates/",
            User.Role.PEMILIH: "/voting/",
        }
        return urls.get(role, "/dashboard/")
