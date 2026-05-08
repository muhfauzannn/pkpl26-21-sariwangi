from django.test import TestCase
from django.urls import reverse

from apps.authentication.models import User

from .forms import CandidateRegistrationForm
from .models import Candidate


class CandidateSecurityTests(TestCase):
    def setUp(self):
        self.pengawas = User.objects.create_user(
            username="pengawas",
            password="StrongPass123!",
            role=User.Role.PENGAWAS,
        )
        self.pemilih = User.objects.create_user(
            username="pemilih",
            password="StrongPass123!",
            role=User.Role.PEMILIH,
        )
        self.paslon = User.objects.create_user(
            username="paslon",
            password="StrongPass123!",
            role=User.Role.PASLON,
        )

    def test_candidate_form_rejects_short_visi_and_misi(self):
        form = CandidateRegistrationForm(
            data={
                "name": "Paslon Aman",
                "visi": "pendek",
                "misi": "singkat",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("visi", form.errors)
        self.assertIn("misi", form.errors)

    def test_pemilih_cannot_register_as_candidate(self):
        self.client.force_login(self.pemilih)

        response = self.client.get(reverse("candidates:register"))

        self.assertEqual(response.status_code, 403)

    def test_pemilih_only_sees_approved_candidates(self):
        Candidate.objects.create(
            user=self.paslon,
            name="Paslon Disetujui",
            visi="Visi yang cukup panjang",
            misi="Misi yang cukup panjang",
            status=Candidate.Status.APPROVED,
            candidate_number=1,
        )
        other_paslon = User.objects.create_user(
            username="paslon2",
            password="StrongPass123!",
            role=User.Role.PASLON,
        )
        pending = Candidate.objects.create(
            user=other_paslon,
            name="Paslon Pending",
            visi="Visi yang cukup panjang",
            misi="Misi yang cukup panjang",
            status=Candidate.Status.PENDING,
        )
        self.client.force_login(self.pemilih)

        list_response = self.client.get(reverse("candidates:list"))
        detail_response = self.client.get(reverse("candidates:detail", args=[pending.pk]))

        self.assertContains(list_response, "Paslon Disetujui")
        self.assertNotContains(list_response, "Paslon Pending")
        self.assertEqual(detail_response.status_code, 404)

    def test_pengawas_can_approve_pending_candidate(self):
        candidate = Candidate.objects.create(
            user=self.paslon,
            name="Paslon Pending",
            visi="Visi yang cukup panjang",
            misi="Misi yang cukup panjang",
        )
        self.client.force_login(self.pengawas)

        response = self.client.post(reverse("candidates:approve", args=[candidate.pk]))
        candidate.refresh_from_db()

        self.assertRedirects(response, reverse("candidates:detail", args=[candidate.pk]))
        self.assertEqual(candidate.status, Candidate.Status.APPROVED)
        self.assertEqual(candidate.candidate_number, 1)
