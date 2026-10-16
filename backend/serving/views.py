import mimetypes
import posixpath

from django.http import Http404, StreamingHttpResponse
from django.views.decorators.http import require_safe

from common.storage import ObjectNotFound, get_object


def _fetch(deploy_id: str, relative_path: str):
    return get_object(f"dist/{deploy_id}/{relative_path}")


@require_safe
def serve_site(request, path=""):
    deploy_id = request.deploy_id

    # normpath on an absolute path collapses any ../ segments, so keys stay inside dist/<id>/
    clean = posixpath.normpath("/" + path).lstrip("/")
    if clean == "" or path.endswith("/"):
        clean = posixpath.join(clean, "index.html")

    try:
        obj = _fetch(deploy_id, clean)
    except ObjectNotFound:
        # Single-page-app fallback: extension-less routes get index.html
        if "." in posixpath.basename(clean):
            raise Http404("File not found")
        clean = "index.html"
        try:
            obj = _fetch(deploy_id, clean)
        except ObjectNotFound:
            raise Http404("Site not found")

    content_type = (
        mimetypes.guess_type(clean)[0]
        or obj.get("ContentType")
        or "application/octet-stream"
    )
    response = StreamingHttpResponse(obj["Body"].iter_chunks(), content_type=content_type)
    if obj.get("ContentLength") is not None:
        response["Content-Length"] = str(obj["ContentLength"])
    return response
