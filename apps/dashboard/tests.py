from django.test import TestCase
from django.urls import reverse

from apps.authentication.models import User
from apps.candidates.models import Candidate
from apps.voters.models import Voter
from apps.voting.models import Vote

from .models import AuditLog


class DashboardAuditTests(TestCase):
    def setUp(self):
        self.pengawas = User.objects.create_user(
            username="pengawas",
            password="StrongPass123!",
            role=User.Role.PENGAWAS,
        )

    def test_login_action_is_written_to_audit_log(self):
        response = self.client.post(
            reverse("authentication:login"),
            {"username": "pengawas", "password": "StrongPass123!"},
        )

        self.assertRedirects(response, reverse("dashboard:home"))
        self.assertTrue(
            AuditLog.objects.filter(user=self.pengawas, action=AuditLog.Action.LOGIN).exists()
        )

    def test_logout_action_is_written_to_audit_log(self):
        self.client.force_login(self.pengawas)

        response = self.client.post(reverse("authentication:logout"))

        self.assertRedirects(response, reverse("authentication:login"))
        self.assertTrue(
            AuditLog.objects.filter(user=self.pengawas, action=AuditLog.Action.LOGOUT).exists()
        )

    def test_audit_log_view_returns_latest_100_entries(self):
        for index in range(101):
            AuditLog.objects.create(
                user=self.pengawas,
                action=AuditLog.Action.LOGIN,
                description=f"Log {index}",
            )
        self.client.force_login(self.pengawas)

        response = self.client.get(reverse("dashboard:audit_log"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["logs"]), 100)

    def test_dashboard_counts_votes_and_voters(self):
        pemilih = User.objects.create_user(
            username="pemilih",
            password="StrongPass123!",
            role=User.Role.PEMILIH,
        )
        Voter.objects.create(
            user=pemilih,
            nik="1234567890123456",
            npm="2106700001",
            email="pemilih@example.com",
            full_name="Pemilih Aman",
            faculty="Ilmu Komputer",
            study_program="Sistem Informasi",
            has_voted=True,
        )
        paslon_user = User.objects.create_user(
            username="paslon",
            password="StrongPass123!",
            role=User.Role.PASLON,
        )
        candidate = Candidate.objects.create(
            user=paslon_user,
            name="Paslon Aman",
            visi="Visi yang cukup panjang",
            misi="Misi yang cukup panjang",
            status=Candidate.Status.APPROVED,
            candidate_number=1,
        )
        Vote.objects.create(voter=pemilih, candidate=candidate)
        self.client.force_login(self.pengawas)

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_votes"], 1)
        self.assertEqual(response.context["voted_count"], 1)
