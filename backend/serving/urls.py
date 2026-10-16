from django.urls import re_path

from .views import serve_site

urlpatterns = [
    re_path(r"^(?P<path>.*)$", serve_site),
]
