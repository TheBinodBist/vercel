
import mimetypes

from django.http import Http404, HttpResponse
from django.views.decorators.http import require_GET

from common.storage import get_object, ObjectNotFound


@require_GET
def serve_site(request, path=""):
    host = request.get_host().split(":")[0].lower()

    # Extract deployment ID from 4s7fw.localhost
    suffix = ".localhost"

    if not host.endswith(suffix):
        raise Http404("Deployment not found")

    deployment_id = host[:-len(suffix)]

    if not deployment_id or "." in deployment_id:
        raise Http404("Invalid deployment hostname")

    # Root URL serves index.html
    file_path = path or "index.html"

    # Prevent unsafe paths
    if (
        "\\" in file_path
        or file_path.startswith("/")
        or ".." in file_path.split("/")
    ):
        raise Http404("Invalid file path")

    key = f"dist/{deployment_id}/{file_path}"

    try:
        obj = get_object(key)
    except ObjectNotFound:
        raise Http404("Site file not found")

    content = obj["Body"].read()

    content_type = (
        obj.get("ContentType")
        or mimetypes.guess_type(file_path)[0]
        or "application/octet-stream"
    )

    return HttpResponse(content, content_type=content_type)
