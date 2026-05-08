from django.test import Client, TestCase
from django.urls import reverse

from apps.authentication.models import User
from apps.candidates.models import Candidate
from apps.voters.models import Voter

from .models import Vote


class VotingSecurityTests(TestCase):
    def setUp(self):
        self.pemilih = User.objects.create_user(
            username="pemilih",
            password="StrongPass123!",
            role=User.Role.PEMILIH,
        )
        Voter.objects.create(
            user=self.pemilih,
            nik="1234567890123456",
            npm="2106700001",
            email="pemilih@example.com",
            full_name="Pemilih Aman",
            faculty="Ilmu Komputer",
            study_program="Sistem Informasi",
        )
        self.paslon_user = User.objects.create_user(
            username="paslon",
            password="StrongPass123!",
            role=User.Role.PASLON,
        )
        self.candidate = Candidate.objects.create(
            user=self.paslon_user,
            name="Paslon Aman",
            visi="Visi yang cukup panjang",
            misi="Misi yang cukup panjang",
            status=Candidate.Status.APPROVED,
            candidate_number=1,
        )

    def test_vote_without_csrf_token_is_rejected(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.pemilih)

        response = client.post(
            reverse("voting:vote"),
            {"candidate": self.candidate.pk},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Vote.objects.count(), 0)

    def test_pemilih_can_vote_once_only(self):
        self.client.force_login(self.pemilih)

        first_response = self.client.post(
            reverse("voting:vote"),
            {"candidate": self.candidate.pk},
        )
        second_response = self.client.post(
            reverse("voting:vote"),
            {"candidate": self.candidate.pk},
        )

        self.assertRedirects(first_response, reverse("voting:success"))
        self.assertRedirects(second_response, reverse("voting:results"))
        self.assertEqual(Vote.objects.filter(voter=self.pemilih).count(), 1)

    def test_results_require_authentication(self):
        response = self.client.get(reverse("voting:results"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("authentication:login"), response["Location"])

    def test_paslon_cannot_access_vote_page(self):
        self.client.force_login(self.paslon_user)

        response = self.client.get(reverse("voting:vote"))

        self.assertEqual(response.status_code, 403)
