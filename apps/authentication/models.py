from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        PEMILIH = "pemilih", "Pemilih"
        PASLON = "paslon", "Paslon"
        PENGAWAS = "pengawas", "Pengawas Pemilu"

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.PEMILIH,
    )

    class Meta:
        db_table = "auth_user"


class LoginAttempt(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="login_attempts",
        null=True,
        blank=True,
    )
    username = models.CharField(max_length=150, db_index=True)
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)

    class Meta:
        db_table = "auth_login_attempt"
        ordering = ["-timestamp"]
