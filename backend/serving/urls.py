from django.urls import path
from .views import serve_site

urlpatterns = [
    path("<str:deployment_id>/", serve_site, name="serve_site"),
    path("<str:deployment_id>/<path:path>", serve_site, name="serve_site_file"),
]
