
from django.contrib import admin
from django.urls import path, include, re_path
from serving.views import serve_site

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("uploads.urls")),

    # Deployment URL with or without trailing slash
    path(
        "site/<str:deployment_id>",
        serve_site,
        name="serve_site",
    ),
    path(
        "site/<str:deployment_id>/",
        serve_site,
    ),

    # Serve deployment assets and nested paths
    path(
        "site/<str:deployment_id>/<path:path>",
        serve_site,
        name="serve_site_file",
    ),

    # Keep the catch-all route last
    re_path(r"^(?P<path>.*)$", serve_site),
]

