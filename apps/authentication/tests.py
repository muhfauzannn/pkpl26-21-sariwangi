from django.test import Client, TestCase
from django.urls import reverse

from .forms import RegistrationForm
from .models import LoginAttempt, User


class AuthenticationSecurityTests(TestCase):
    def test_registration_rejects_pengawas_role_from_public_form(self):
        form = RegistrationForm(
            data={
                "username": "pengawas_public",
                "email": "pengawas-public@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "role": User.Role.PENGAWAS,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("role", form.errors)

    def test_registration_uses_django_password_validators(self):
        form = RegistrationForm(
            data={
                "username": "pemilih1",
                "email": "pemilih1@example.com",
                "password1": "password",
                "password2": "password",
                "role": User.Role.PEMILIH,
                "nik": "1234567890123456",
                "npm": "2106700001",
                "faculty": "Ilmu Komputer",
                "study_program": "Sistem Informasi",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_login_rate_limit_locks_unknown_username_after_five_failures(self):
        client = Client()
        login_url = reverse("authentication:login")

        for _ in range(5):
            response = client.post(
                login_url,
                {"username": "ghost", "password": "wrong"},
            )
            self.assertContains(response, "Username atau password salah.", status_code=200)

        response = client.post(
            login_url,
            {"username": "ghost", "password": "wrong"},
        )

        self.assertContains(
            response,
            "Akun sementara dikunci. Coba lagi dalam 15 menit.",
            status_code=200,
        )
        self.assertEqual(
            LoginAttempt.objects.filter(username__iexact="ghost", success=False).count(),
            5,
        )

    def test_logout_without_csrf_token_is_rejected(self):
        user = User.objects.create_user(
            username="pemilih",
            password="StrongPass123!",
            role=User.Role.PEMILIH,
        )
        client = Client(enforce_csrf_checks=True)
        client.force_login(user)

        response = client.post(reverse("authentication:logout"))

        self.assertEqual(response.status_code, 403)
