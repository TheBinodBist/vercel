import logging
import shutil
import subprocess
from pathlib import Path

from django.conf import settings

from common.storage import download_prefix, upload_folder

logger = logging.getLogger(__name__)


class BuildError(Exception):
    pass


def _run(cmd, cwd):
    logger.info("$ %s (in %s)", " ".join(cmd), cwd)
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=settings.BUILD_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise BuildError(f"`{' '.join(cmd)}` timed out") from exc
    if proc.stdout:
        logger.info("stdout: %s", proc.stdout)
    if proc.stderr:
        logger.info("stderr: %s", proc.stderr)
    if proc.returncode != 0:
        raise BuildError(f"`{' '.join(cmd)}` exited with code {proc.returncode}")


def build_project(project_dir: Path) -> None:
    npm = shutil.which("npm")
    if not npm:
        raise BuildError("npm is not installed on this worker")
    _run([npm, "install"], project_dir)
    _run([npm, "run", "build"], project_dir)


def process_deployment(deploy_id: str) -> None:
    """Download sources -> build -> upload the build output to dist/<id>/."""
    work_root = Path(settings.WORK_DIR)
    project_dir = work_root / "output" / deploy_id
    try:
        count = download_prefix(f"output/{deploy_id}/", work_root)
        if count == 0:
            raise BuildError(f"No source files found in storage for {deploy_id}")

        build_project(project_dir)

        dist_dir = project_dir / settings.BUILD_OUTPUT_DIR
        if not dist_dir.is_dir():
            raise BuildError(f"Build produced no '{settings.BUILD_OUTPUT_DIR}' directory")
        upload_folder(dist_dir, f"dist/{deploy_id}")
    finally:
        shutil.rmtree(project_dir, ignore_errors=True)
