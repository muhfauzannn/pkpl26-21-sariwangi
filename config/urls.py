from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path
from django.views.generic import RedirectView

from apps.authentication.models import User


@login_required
def home_redirect(request):
    role_urls = {
        User.Role.PENGAWAS: "/dashboard/",
        User.Role.PASLON: "/candidates/",
        User.Role.PEMILIH: "/voting/",
    }
    from django.shortcuts import redirect
    return redirect(role_urls.get(request.user.role, "/dashboard/"))


urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include("apps.authentication.urls")),
    path("voters/", include("apps.voters.urls")),
    path("candidates/", include("apps.candidates.urls")),
    path("voting/", include("apps.voting.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("", home_redirect, name="home"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
