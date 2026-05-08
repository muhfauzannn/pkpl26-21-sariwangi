from django.test import TestCase
from django.urls import reverse

from apps.authentication.models import User
from apps.dashboard.models import AuditLog

from .forms import CandidateMemberForm, CandidateRegistrationForm
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

    def test_candidate_forms_strip_valid_text(self):
        candidate_form = CandidateRegistrationForm(
            data={
                "name": "  Paslon Aman  ",
                "visi": "  Visi yang cukup panjang  ",
                "misi": "  Misi yang cukup panjang  ",
            }
        )
        member_form = CandidateMemberForm(
            data={
                "name": "  Anggota Satu  ",
                "role": "  Calon Ketua  ",
            }
        )

        self.assertTrue(candidate_form.is_valid())
        self.assertTrue(member_form.is_valid())
        self.assertEqual(candidate_form.cleaned_data["name"], "Paslon Aman")
        self.assertEqual(candidate_form.cleaned_data["visi"], "Visi yang cukup panjang")
        self.assertEqual(candidate_form.cleaned_data["misi"], "Misi yang cukup panjang")
        self.assertEqual(member_form.cleaned_data["name"], "Anggota Satu")
        self.assertEqual(member_form.cleaned_data["role"], "Calon Ketua")

    def test_pemilih_cannot_register_as_candidate(self):
        self.client.force_login(self.pemilih)

        response = self.client.get(reverse("candidates:register"))

        self.assertEqual(response.status_code, 403)

    def test_non_pengawas_cannot_approve_or_reject_candidate(self):
        candidate = Candidate.objects.create(
            user=self.paslon,
            name="Paslon Pending",
            visi="Visi yang cukup panjang",
            misi="Misi yang cukup panjang",
        )
        self.client.force_login(self.pemilih)

        approve_response = self.client.post(reverse("candidates:approve", args=[candidate.pk]))
        reject_response = self.client.post(reverse("candidates:reject", args=[candidate.pk]))

        self.assertEqual(approve_response.status_code, 403)
        self.assertEqual(reject_response.status_code, 403)

    def test_paslon_cannot_register_twice(self):
        Candidate.objects.create(
            user=self.paslon,
            name="Paslon Terdaftar",
            visi="Visi yang cukup panjang",
            misi="Misi yang cukup panjang",
        )
        self.client.force_login(self.paslon)

        response = self.client.get(reverse("candidates:register"))

        self.assertRedirects(response, reverse("candidates:list"))

    def test_paslon_can_open_candidate_register_form(self):
        self.client.force_login(self.paslon)

        response = self.client.get(reverse("candidates:register"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("member_formset", response.context)

    def test_paslon_can_register_candidate_with_members(self):
        self.client.force_login(self.paslon)

        response = self.client.post(
            reverse("candidates:register"),
            {
                "name": "  Paslon Baru  ",
                "visi": "Visi yang cukup panjang",
                "misi": "Misi yang cukup panjang",
                "members-TOTAL_FORMS": "1",
                "members-INITIAL_FORMS": "0",
                "members-MIN_NUM_FORMS": "0",
                "members-MAX_NUM_FORMS": "5",
                "members-0-name": "Anggota Satu",
                "members-0-role": "Calon Ketua",
            },
        )

        self.assertRedirects(response, reverse("candidates:list"))
        candidate = Candidate.objects.get(user=self.paslon)
        self.assertEqual(candidate.name, "Paslon Baru")
        self.assertEqual(candidate.members.count(), 1)
        self.assertTrue(
            AuditLog.objects.filter(action=AuditLog.Action.CANDIDATE_REGISTER).exists()
        )

    def test_candidate_register_rerenders_when_member_formset_invalid(self):
        self.client.force_login(self.paslon)

        response = self.client.post(
            reverse("candidates:register"),
            {
                "name": "Paslon Baru",
                "visi": "Visi yang cukup panjang",
                "misi": "Misi yang cukup panjang",
                "members-TOTAL_FORMS": "1",
                "members-INITIAL_FORMS": "0",
                "members-MIN_NUM_FORMS": "0",
                "members-MAX_NUM_FORMS": "5",
                "members-0-name": "Anggota Tanpa Role",
                "members-0-role": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Candidate.objects.filter(user=self.paslon).exists())

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

    def test_paslon_only_sees_own_candidate_detail(self):
        own = Candidate.objects.create(
            user=self.paslon,
            name="Paslon Sendiri",
            visi="Visi yang cukup panjang",
            misi="Misi yang cukup panjang",
        )
        other_user = User.objects.create_user(
            username="paslon_lain",
            password="StrongPass123!",
            role=User.Role.PASLON,
        )
        other = Candidate.objects.create(
            user=other_user,
            name="Paslon Lain",
            visi="Visi yang cukup panjang",
            misi="Misi yang cukup panjang",
        )
        self.client.force_login(self.paslon)

        own_response = self.client.get(reverse("candidates:detail", args=[own.pk]))
        other_response = self.client.get(reverse("candidates:detail", args=[other.pk]))

        self.assertEqual(own_response.status_code, 200)
        self.assertEqual(other_response.status_code, 404)

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
        self.assertTrue(
            AuditLog.objects.filter(action=AuditLog.Action.CANDIDATE_APPROVE).exists()
        )

    def test_pengawas_can_reject_pending_candidate(self):
        candidate = Candidate.objects.create(
            user=self.paslon,
            name="Paslon Pending",
            visi="Visi yang cukup panjang",
            misi="Misi yang cukup panjang",
        )
        self.client.force_login(self.pengawas)

        response = self.client.post(reverse("candidates:reject", args=[candidate.pk]))
        candidate.refresh_from_db()

        self.assertRedirects(response, reverse("candidates:detail", args=[candidate.pk]))
        self.assertEqual(candidate.status, Candidate.Status.REJECTED)
        self.assertTrue(
            AuditLog.objects.filter(action=AuditLog.Action.CANDIDATE_REJECT).exists()
        )

    def test_approved_candidate_cannot_be_approved_again(self):
        candidate = Candidate.objects.create(
            user=self.paslon,
            name="Paslon Approved",
            visi="Visi yang cukup panjang",
            misi="Misi yang cukup panjang",
            status=Candidate.Status.APPROVED,
            candidate_number=1,
        )
        self.client.force_login(self.pengawas)

        response = self.client.post(reverse("candidates:approve", args=[candidate.pk]))
        candidate.refresh_from_db()

        self.assertRedirects(response, reverse("candidates:detail", args=[candidate.pk]))
        self.assertEqual(candidate.candidate_number, 1)

    def test_rejected_candidate_cannot_be_rejected_again(self):
        candidate = Candidate.objects.create(
            user=self.paslon,
            name="Paslon Rejected",
            visi="Visi yang cukup panjang",
            misi="Misi yang cukup panjang",
            status=Candidate.Status.REJECTED,
        )
        self.client.force_login(self.pengawas)

        response = self.client.post(reverse("candidates:reject", args=[candidate.pk]))

        self.assertRedirects(response, reverse("candidates:detail", args=[candidate.pk]))
