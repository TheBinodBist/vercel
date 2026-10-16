from django.conf import settings

from common.ids import is_valid_id


class SubdomainRoutingMiddleware:
    """Requests to <id>.BASE_DOMAIN are served from the deployed site; everything else hits the API."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0].lower()
        suffix = "." + settings.BASE_DOMAIN.lower()
        if host.endswith(suffix):
            subdomain = host[: -len(suffix)].split(".")[-1]
            if is_valid_id(subdomain):
                request.urlconf = "serving.urls"
                request.deploy_id = subdomain
        return self.get_response(request)
