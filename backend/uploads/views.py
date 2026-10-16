import logging
import shutil
from pathlib import Path

from django.conf import settings
from git import Repo
from git.exc import GitCommandError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from common.ids import generate_id, is_valid_id
from common.redis_client import BUILD_QUEUE, STATUS_HASH, get_redis
from common.storage import upload_folder

from .serializers import DeploySerializer

logger = logging.getLogger(__name__)


class DeployView(APIView):

    def post(self, request):
        serializer = DeploySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        repo_url = serializer.validated_data["repoUrl"]

        r = get_redis()
        deploy_id = generate_id()
        while r.hexists(STATUS_HASH, deploy_id):
            deploy_id = generate_id()

        clone_dir = Path(settings.WORK_DIR) / "output" / deploy_id
        try:
            Repo.clone_from(repo_url, clone_dir, depth=1)
            # Uploaded synchronously, so the queue is only fed once every file is in storage.
            upload_folder(clone_dir, f"output/{deploy_id}", skip_dirs=(".git",))
        except GitCommandError:
            logger.exception("Clone failed for %s", repo_url)
            return Response(
                {"error": "Could not clone the repository."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        finally:
            shutil.rmtree(clone_dir, ignore_errors=True)

        r.hset(STATUS_HASH, deploy_id, "uploaded")
        r.lpush(BUILD_QUEUE, deploy_id)
        return Response({"id": deploy_id})


class StatusView(APIView):
    """GET /api/status/?id=ab12c  ->  {"status": "uploaded" | "building" | "deployed" | "failed" | null}"""

    def get(self, request):
        deploy_id = request.query_params.get("id", "")
        if not is_valid_id(deploy_id):
            return Response(
                {"error": "A valid 'id' query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"status": get_redis().hget(STATUS_HASH, deploy_id)})
