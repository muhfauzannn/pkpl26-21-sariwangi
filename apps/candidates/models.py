from django.conf import settings
from django.db import models


class Candidate(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="candidate_profile",
    )
    candidate_number = models.PositiveIntegerField(unique=True, null=True, blank=True)
    name = models.CharField(max_length=150)
    photo = models.ImageField(upload_to="candidates/photos/", blank=True)
    visi = models.TextField()
    misi = models.TextField()
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_candidates",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "candidates_candidate"


class CandidateMember(models.Model):
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="members",
    )
    name = models.CharField(max_length=150)
    role = models.CharField(max_length=50)
    photo = models.ImageField(upload_to="candidates/members/", blank=True)

    class Meta:
        db_table = "candidates_member"
