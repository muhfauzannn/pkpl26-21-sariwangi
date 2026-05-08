from django.test import TestCase
from django.urls import reverse

from apps.authentication.models import User
from apps.dashboard.models import AuditLog

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

    def test_pengawas_can_create_update_and_delete_voter(self):
        pengawas = User.objects.create_user(
            username="pengawas",
            password="StrongPass123!",
            role=User.Role.PENGAWAS,
        )
        self.client.force_login(pengawas)

        create_response = self.client.post(
            reverse("voters:create"),
            {
                "nik": "1234567890123456",
                "npm": "2106700001",
                "email": "pemilih@example.com",
                "full_name": "Pemilih Aman",
                "faculty": "Ilmu Komputer",
                "study_program": "Sistem Informasi",
                "status": Voter.Status.ACTIVE,
            },
        )
        voter = Voter.objects.get(nik="1234567890123456")
        update_response = self.client.post(
            reverse("voters:update", args=[voter.pk]),
            {
                "nik": voter.nik,
                "npm": voter.npm,
                "email": voter.email,
                "full_name": "Pemilih Aman Update",
                "faculty": voter.faculty,
                "study_program": voter.study_program,
                "status": Voter.Status.ACTIVE,
            },
        )
        delete_response = self.client.post(reverse("voters:delete", args=[voter.pk]))

        self.assertRedirects(create_response, reverse("voters:list"))
        self.assertRedirects(update_response, reverse("voters:list"))
        self.assertRedirects(delete_response, reverse("voters:list"))
        self.assertFalse(Voter.objects.filter(pk=voter.pk).exists())
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.VOTER_CREATE).exists())
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.VOTER_UPDATE).exists())
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.VOTER_DELETE).exists())

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

    def test_template_escapes_dangerous_voter_input(self):
        pengawas = User.objects.create_user(
            username="pengawas",
            password="StrongPass123!",
            role=User.Role.PENGAWAS,
        )
        Voter.objects.create(
            nik="1234567890123456",
            npm="2106700001",
            email="pemilih@example.com",
            full_name="<script>alert(1)</script>",
            faculty="Ilmu Komputer",
            study_program="Sistem Informasi",
        )
        self.client.force_login(pengawas)

        response = self.client.get(reverse("voters:list"))

        self.assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;")
        self.assertNotContains(response, "<script>alert(1)</script>", html=False)
