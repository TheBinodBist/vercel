
# import mimetypes

# from django.http import Http404, HttpResponse
# from django.views.decorators.http import require_GET

# from common.storage import get_object, ObjectNotFound


# @require_GET
# def serve_site(request, deployment_id=None, path=""):
#     host = request.get_host().split(":")[0].lower()


#     suffix = ".localhost"

#     if deployment_id is None:
#         if not host.endswith(suffix):
#             raise Http404("Deployment not found")

#         deployment_id = host[:-len(suffix)]

#     # Validate deployment ID
#     if (
#         not deployment_id
#         or not deployment_id.isalnum()
#         or len(deployment_id) > 20
#     ):
#         raise Http404("Invalid deployment ID")

#     # Root URL serves index.html
#     file_path = path or "index.html"

#     # Prevent unsafe paths
#     if (
#         "\\" in file_path
#         or file_path.startswith("/")
#         or ".." in file_path.split("/")
#     ):
#         raise Http404("Invalid file path")

#     key = f"dist/{deployment_id}/{file_path}"

#     try:
#         obj = get_object(key)
#     except ObjectNotFound:
#         raise Http404("Site file not found")

#     content = obj["Body"].read()

#     content_type = (
#         obj.get("ContentType")
#         or mimetypes.guess_type(file_path)[0]
#         or "application/octet-stream"
#     )

#     return HttpResponse(content, content_type=content_type)




import mimetypes

from django.http import Http404, HttpResponse
from django.views.decorators.http import require_GET

from common.storage import get_object, ObjectNotFound


@require_GET
def serve_site(request, deployment_id=None, path=""):
    host = request.get_host().split(":")[0].lower()

    # Support local subdomains such as wa1eu.localhost
    if deployment_id is None:
        suffix = ".localhost"

        if not host.endswith(suffix):
            raise Http404("Deployment not found")

        deployment_id = host[:-len(suffix)]

    # Validate deployment ID
    if (
        not deployment_id
        or not deployment_id.isalnum()
        or len(deployment_id) > 20
    ):
        raise Http404("Invalid deployment ID")

    # Serve index.html for the deployment root
    file_path = path or "index.html"

    # Prevent unsafe paths
    if (
        "\\" in file_path
        or file_path.startswith("/")
        or ".." in file_path.split("/")
    ):
        raise Http404("Invalid file path")

    # Fetch the built file from Cloudflare R2
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

