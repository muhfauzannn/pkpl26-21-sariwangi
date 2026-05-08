from django.conf import settings
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse


class RoleBasedAccessControlMiddleware:
    PUBLIC_PATHS = [
        "/auth/login/",
        "/auth/register/",
        "/admin/",
        "/static/",
        "/media/",
        "/voting/results/",
    ]

    ROLE_PATHS = {
        "pengawas": ["/"],
        "pemilih": ["/voting/", "/candidates/", "/auth/logout/"],
        "paslon": ["/candidates/", "/voting/results/", "/auth/logout/"],
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        if self._is_public_path(path):
            return self.get_response(request)

        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        if not self._is_path_allowed(request.user.role, path):
            return HttpResponseForbidden("Anda tidak memiliki akses ke halaman ini.")

        return self.get_response(request)

    def _is_public_path(self, path):
        return any(path.startswith(prefix) for prefix in self.PUBLIC_PATHS)

    def _is_path_allowed(self, role, path):
        if role == "pengawas":
            return True

        allowed = self.ROLE_PATHS.get(role, [])
        return any(path.startswith(prefix) for prefix in allowed)
