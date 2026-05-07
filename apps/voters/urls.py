from django.urls import path

from . import views

app_name = "voters"

urlpatterns = [
    path("", views.VoterListView.as_view(), name="list"),
    path("create/", views.VoterCreateView.as_view(), name="create"),
    path("<int:pk>/update/", views.VoterUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.VoterDeleteView.as_view(), name="delete"),
]
