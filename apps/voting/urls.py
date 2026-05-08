from django.urls import path

from . import views

app_name = "voting"

urlpatterns = [
    path("", views.VotingView.as_view(), name="vote"),
    path("success/", views.VoteSuccessView.as_view(), name="success"),
    path("results/", views.VotingResultsView.as_view(), name="results"),
]
