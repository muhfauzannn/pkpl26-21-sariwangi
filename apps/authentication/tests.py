from unittest.mock import patch

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from apps.voters.models import Voter

from .forms import RegistrationForm
from .models import LoginAttempt, User
from .services import get_client_ip, perform_login


class AuthenticationSecurityTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def _request_with_session(self):
        request = self.factory.post(reverse("authentication:login"))
        SessionMiddleware(lambda req: None).process_request(request)
        request.session.save()
        return request

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

    def test_registration_rejects_duplicate_identity_fields(self):
        user = User.objects.create_user(
            username="pemilih1",
            email="pemilih1@example.com",
            password="StrongPass123!",
            role=User.Role.PEMILIH,
        )
        Voter.objects.create(
            user=user,
            nik="1234567890123456",
            npm="2106700001",
            email=user.email,
            full_name="Pemilih Satu",
            faculty="Ilmu Komputer",
            study_program="Sistem Informasi",
        )

        form = RegistrationForm(
            data={
                "username": "PEMILIH1",
                "email": "PEMILIH1@example.com",
                "first_name": "  Pemilih  ",
                "last_name": "  Dua  ",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "role": User.Role.PEMILIH,
                "nik": "1234567890123456",
                "npm": "2106700001",
                "faculty": "",
                "study_program": "",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)
        self.assertIn("email", form.errors)
        self.assertIn("nik", form.errors)
        self.assertIn("npm", form.errors)
        self.assertIn("faculty", form.errors)
        self.assertIn("study_program", form.errors)

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

    def test_registration_rejects_password_mismatch_and_invalid_voter_numbers(self):
        form = RegistrationForm(
            data={
                "username": "pemilih_invalid",
                "email": "pemilih-invalid@example.com",
                "password1": "StrongPass123!",
                "password2": "DifferentPass123!",
                "role": User.Role.PEMILIH,
                "nik": "123",
                "npm": "21ABC",
                "faculty": "Ilmu Komputer",
                "study_program": "Sistem Informasi",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)
        self.assertIn("nik", form.errors)
        self.assertIn("npm", form.errors)

    def test_create_user_stores_hashed_password(self):
        user = User.objects.create_user(
            username="hashed_user",
            password="StrongPass123!",
            role=User.Role.PEMILIH,
        )

        self.assertNotEqual(user.password, "StrongPass123!")
        self.assertTrue(user.password.startswith("pbkdf2_"))
        self.assertTrue(user.check_password("StrongPass123!"))

    def test_registration_creates_pemilih_profile(self):
        response = self.client.post(
            reverse("authentication:register"),
            {
                "username": "pemilih2",
                "email": "pemilih2@example.com",
                "first_name": "  Pemilih  ",
                "last_name": "  Dua  ",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "role": User.Role.PEMILIH,
                "nik": "1234567890123456",
                "npm": "2106700001",
                "faculty": "Ilmu Komputer",
                "study_program": "Sistem Informasi",
            },
        )

        self.assertRedirects(response, reverse("authentication:login"))
        user = User.objects.get(username="pemilih2")
        self.assertEqual(user.first_name, "Pemilih")
        self.assertTrue(Voter.objects.filter(user=user, nik="1234567890123456").exists())

    def test_registration_creates_paslon_without_voter_profile(self):
        response = self.client.post(
            reverse("authentication:register"),
            {
                "username": "paslon_public",
                "email": "paslon-public@example.com",
                "first_name": "Paslon",
                "last_name": "Publik",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "role": User.Role.PASLON,
            },
        )

        self.assertRedirects(response, reverse("authentication:login"))
        self.assertFalse(Voter.objects.filter(user__username="paslon_public").exists())

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

    def test_get_client_ip_uses_forwarded_for(self):
        request = self.factory.get("/", HTTP_X_FORWARDED_FOR="203.0.113.10, 10.0.0.1")

        self.assertEqual(get_client_ip(request), "203.0.113.10")

    def test_inactive_login_attempt_returns_disabled_error_when_backend_returns_user(self):
        user = User.objects.create_user(
            username="inactive",
            password="StrongPass123!",
            role=User.Role.PEMILIH,
            is_active=False,
        )
        request = self._request_with_session()

        with patch("apps.authentication.services.auth.authenticate", return_value=user):
            logged_in_user, error = perform_login(request, "inactive", "StrongPass123!")

        self.assertIsNone(logged_in_user)
        self.assertEqual(error, "Akun dinonaktifkan.")
        self.assertTrue(LoginAttempt.objects.filter(username="inactive", success=False).exists())

    def test_authenticated_users_are_redirected_away_from_auth_pages(self):
        pemilih = User.objects.create_user(
            username="pemilih_redirect",
            password="StrongPass123!",
            role=User.Role.PEMILIH,
        )
        self.client.force_login(pemilih)

        login_response = self.client.get(reverse("authentication:login"))
        register_response = self.client.get(reverse("authentication:register"))

        self.assertEqual(login_response["Location"], "/voting/")
        self.assertEqual(register_response["Location"], "/voting/")

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
