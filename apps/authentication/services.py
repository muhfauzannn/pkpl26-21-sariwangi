from datetime import timedelta

from django.contrib import auth
from django.utils import timezone

from .models import LoginAttempt

LOCKOUT_THRESHOLD = 5
LOCKOUT_WINDOW_MINUTES = 15


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


def get_recent_failed_attempts(username, ip_address):
    window = timezone.now() - timedelta(minutes=LOCKOUT_WINDOW_MINUTES)
    return LoginAttempt.objects.filter(
        username__iexact=username.strip(),
        ip_address=ip_address,
        success=False,
        timestamp__gte=window,
    ).count()


def is_account_locked(username, ip_address):
    return get_recent_failed_attempts(username, ip_address) >= LOCKOUT_THRESHOLD


def record_login_attempt(username, user, ip_address, success):
    return LoginAttempt.objects.create(
        username=username.strip(),
        user=user,
        ip_address=ip_address,
        success=success,
    )


def perform_login(request, username, password):
    ip_address = get_client_ip(request)
    username = username.strip()

    if is_account_locked(username, ip_address):
        return None, "Akun sementara dikunci. Coba lagi dalam 15 menit."

    user = auth.authenticate(request, username=username, password=password)

    if user is None:
        existing = auth.get_user_model().objects.filter(username__iexact=username).first()
        record_login_attempt(username, existing, ip_address, success=False)
        return None, "Username atau password salah."

    if not user.is_active:
        record_login_attempt(username, user, ip_address, success=False)
        return None, "Akun dinonaktifkan."

    record_login_attempt(username, user, ip_address, success=True)
    auth.login(request, user)
    return user, None


def perform_logout(request):
    auth.logout(request)
