from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="home"),
    path("audit-log/", views.AuditLogListView.as_view(), name="audit_log"),
]
