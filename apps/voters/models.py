from django.conf import settings
from django.db import models


class Voter(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="voter_profile",
    )
    nik = models.CharField(max_length=16, unique=True)
    npm = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150)
    faculty = models.CharField(max_length=100)
    study_program = models.CharField(max_length=100)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    has_voted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "voters_voter"
