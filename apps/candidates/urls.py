from django.urls import path

from . import views

app_name = "candidates"

urlpatterns = [
    path("", views.CandidateListView.as_view(), name="list"),
    path("register/", views.CandidateRegisterView.as_view(), name="register"),
    path("<int:pk>/", views.CandidateDetailView.as_view(), name="detail"),
    path("<int:pk>/approve/", views.CandidateApproveView.as_view(), name="approve"),
    path("<int:pk>/reject/", views.CandidateRejectView.as_view(), name="reject"),
]
