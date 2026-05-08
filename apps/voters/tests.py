from django.test import TestCase
from django.urls import reverse

from apps.authentication.models import User

from .forms import VoterForm
from .models import Voter


class VoterSecurityTests(TestCase):
    def test_voter_form_rejects_invalid_nik_and_npm(self):
        form = VoterForm(
            data={
                "nik": "123",
                "npm": "21ABC",
                "email": "pemilih@example.com",
                "full_name": "Pemilih Aman",
                "faculty": "Ilmu Komputer",
                "study_program": "Sistem Informasi",
                "status": Voter.Status.ACTIVE,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("nik", form.errors)
        self.assertIn("npm", form.errors)

    def test_non_pengawas_cannot_access_voter_management(self):
        user = User.objects.create_user(
            username="pemilih",
            password="StrongPass123!",
            role=User.Role.PEMILIH,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("voters:list"))

        self.assertEqual(response.status_code, 403)

    def test_voter_form_rejects_duplicate_email_case_insensitive(self):
        Voter.objects.create(
            nik="1234567890123456",
            npm="2106700001",
            email="pemilih@example.com",
            full_name="Pemilih Satu",
            faculty="Ilmu Komputer",
            study_program="Sistem Informasi",
        )

        form = VoterForm(
            data={
                "nik": "1234567890123457",
                "npm": "2106700002",
                "email": "PEMILIH@example.com",
                "full_name": "Pemilih Dua",
                "faculty": "Ilmu Komputer",
                "study_program": "Sistem Informasi",
                "status": Voter.Status.ACTIVE,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
