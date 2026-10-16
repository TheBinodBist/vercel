from django.urls import path

from .views import DeployView, StatusView

urlpatterns = [
    path("deploy/", DeployView.as_view()),
    path("status/", StatusView.as_view()),
]
