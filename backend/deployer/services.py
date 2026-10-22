
import logging
import shutil
import subprocess
from pathlib import Path

from django.conf import settings

from common.storage import download_prefix, upload_folder

logger = logging.getLogger(__name__)

OUTPUT_DIR_CANDIDATES = ("dist", "build")


class BuildError(Exception):
    pass


def _run(cmd, cwd):
    logger.info("$ %s (in %s)", " ".join(cmd), cwd)

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=settings.BUILD_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise BuildError(
            f"Command timed out: {' '.join(cmd)}"
        ) from exc
    except OSError as exc:
        raise BuildError(
            f"Could not run command {' '.join(cmd)}: {exc}"
        ) from exc

    if proc.stdout:
        logger.info("stdout: %s", proc.stdout)

    if proc.stderr:
        logger.info("stderr: %s", proc.stderr)

    if proc.returncode != 0:
        raise BuildError(
            f"Command failed: {' '.join(cmd)} "
            f"(exit code {proc.returncode})"
        )


def build_project(project_dir: Path, deploy_id: str) -> None:
    """Install dependencies and build the project for its deployment URL."""

    npm = shutil.which("npm") or shutil.which("npm.cmd")

    if not npm:
        raise BuildError("npm is not installed or not available in PATH")

    if not (project_dir / "package.json").is_file():
        raise BuildError(f"package.json not found in {project_dir}")

    flags = ["--no-audit", "--no-fund"]

    if (project_dir / "package-lock.json").exists():
        _run([npm, "ci", *flags], project_dir)
    else:
        _run([npm, "install", *flags], project_dir)

    _run(
        [
            npm,
            "run",
            "build",
            "--",
            "--base",
            f"/site/{deploy_id}/",
        ],
        project_dir,
    )


def find_output_dir(project_dir: Path) -> Path:
    """Find the production output directory containing index.html."""

    configured = getattr(settings, "BUILD_OUTPUT_DIR", "dist")

    names = [
        configured,
        *(name for name in OUTPUT_DIR_CANDIDATES if name != configured),
    ]

    for name in names:
        candidate = project_dir / name

        if candidate.is_dir() and (candidate / "index.html").is_file():
            return candidate

    raise BuildError(
        "Build finished, but no output folder containing index.html "
        f"was found. Checked: {', '.join(names)}"
    )


def process_deployment(deploy_id: str) -> None:
    """Download source from R2, build it, and upload production files."""

    work_root = Path(settings.WORK_DIR).resolve()
    project_dir = (work_root / "output" / deploy_id).resolve()

    if not deploy_id.isalnum() or len(deploy_id) > 20:
        raise BuildError("Invalid deployment ID")

    if not project_dir.is_relative_to(work_root):
        raise BuildError("Invalid deployment path")

    try:
        # Step 1: Download source code from R2.
        count = download_prefix(
            f"output/{deploy_id}/",
            work_root,
        )

        if count == 0:
            raise BuildError(
                f"No source files found for deployment {deploy_id}"
            )

        logger.info(
            "Downloaded %s source files for %s",
            count,
            deploy_id,
        )

        # Step 2: Install dependencies and build the project.
        build_project(project_dir, deploy_id)

        # Step 3: Locate the production build directory.
        build_dir = find_output_dir(project_dir)

        logger.info("Build output directory: %s", build_dir)

        # Step 4: Upload production files to R2.
        uploaded = upload_folder(
            build_dir,
            f"dist/{deploy_id}",
        )

        if not uploaded:
            raise BuildError("No production files were uploaded")

        logger.info(
            "Deployment %s uploaded %s production files",
            deploy_id,
            uploaded,
        )

    finally:
        # Step 5: Remove temporary deployment files.
        shutil.rmtree(project_dir, ignore_errors=True)

