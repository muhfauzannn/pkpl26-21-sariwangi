from unittest.mock import patch

from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.db import IntegrityError
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from apps.authentication.models import User
from apps.candidates.models import Candidate
from apps.dashboard.models import AuditLog
from apps.voters.models import Voter

from .models import Vote
from .views import VotingView


class VotingSecurityTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
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

    def _request_for_user(self, user):
        request = self.factory.get(reverse("voting:vote"))
        request.user = user
        SessionMiddleware(lambda req: None).process_request(request)
        request.session.save()
        request._messages = FallbackStorage(request)
        return request

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
        self.assertTrue(AuditLog.objects.filter(action=AuditLog.Action.VOTE).exists())

    def test_results_require_authentication(self):
        response = self.client.get(reverse("voting:results"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("authentication:login"), response["Location"])

    def test_paslon_cannot_access_vote_page(self):
        request = self._request_for_user(self.paslon_user)

        response = VotingView.as_view()(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/")

    def test_vote_page_lists_approved_candidates(self):
        self.client.force_login(self.pemilih)

        response = self.client.get(reverse("voting:vote"))

        self.assertContains(response, "Paslon Aman")

    def test_pemilih_without_voter_profile_cannot_vote(self):
        no_profile = User.objects.create_user(
            username="no_profile",
            password="StrongPass123!",
            role=User.Role.PEMILIH,
        )
        self.client.force_login(no_profile)

        response = self.client.get(reverse("voting:vote"))

        self.assertRedirects(response, reverse("voting:results"))

    def test_inactive_voter_cannot_vote(self):
        Voter.objects.filter(user=self.pemilih).update(status=Voter.Status.INACTIVE)
        self.client.force_login(self.pemilih)

        response = self.client.get(reverse("voting:vote"))

        self.assertRedirects(response, reverse("voting:results"))

    def test_integrity_error_during_vote_redirects_to_results(self):
        self.client.force_login(self.pemilih)

        with patch("apps.voting.views.Vote.objects.create", side_effect=IntegrityError):
            response = self.client.post(
                reverse("voting:vote"),
                {"candidate": self.candidate.pk},
            )

        self.assertRedirects(response, reverse("voting:results"))
        self.assertEqual(Vote.objects.count(), 0)

    def test_results_show_vote_count(self):
        Vote.objects.create(voter=self.pemilih, candidate=self.candidate)
        self.client.force_login(self.pemilih)

        response = self.client.get(reverse("voting:results"))

        self.assertContains(response, "Paslon Aman")
        self.assertContains(response, "1")
