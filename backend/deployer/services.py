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


def build_project(project_dir: Path) -> None:
    npm = shutil.which("npm") or shutil.which("npm.cmd")

    if not npm:
        raise BuildError("npm is not installed or not available in PATH")

    if not (project_dir / "package.json").is_file():
        raise BuildError(
            f"package.json not found in {project_dir}"
        )

    flags = ["--no-audit", "--no-fund"]

    if (project_dir / "package-lock.json").exists():
        _run([npm, "ci", *flags], project_dir)
    else:
        _run([npm, "install", *flags], project_dir)

    _run([npm, "run", "build"], project_dir)


def find_output_dir(project_dir: Path) -> Path:
    configured = getattr(settings, "BUILD_OUTPUT_DIR", "dist")

    names = [
        configured,
        *(
            name
            for name in OUTPUT_DIR_CANDIDATES
            if name != configured
        ),
    ]

    for name in names:
        candidate = project_dir / name

        if (
            candidate.is_dir()
            and (candidate / "index.html").is_file()
        ):
            return candidate

    raise BuildError(
        "Build finished, but no output folder containing index.html "
        f"was found. Checked: {', '.join(names)}"
    )


def process_deployment(deploy_id: str) -> None:
    """Download source -> build -> upload production files to R2."""

    work_root = Path(settings.WORK_DIR).resolve()
    project_dir = (work_root / "output" / deploy_id).resolve()

    # Prevent an invalid deployment ID from escaping WORK_DIR.
    if not project_dir.is_relative_to(work_root):
        raise BuildError("Invalid deployment ID")

    try:
        # Download the source files from R2.
        count = download_prefix(
            f"output/{deploy_id}/",
            work_root,
        )

        if count == 0:
            raise BuildError(
                f"No source files found in R2 for deployment {deploy_id}"
            )

        # Compile React/Vite/Create React App.
        build_project(project_dir)

        # Locate the production folder.
        build_dir = find_output_dir(project_dir)

        logger.info("Build output: %s", build_dir)

        # Upload built HTML, CSS, JavaScript and assets.
        # This prefix must match your serving view.
        uploaded = upload_folder(
            build_dir,
            f"output/{deploy_id}",
        )

        logger.info(
            "Deployment %s uploaded %s production files",
            deploy_id,
            uploaded,
        )

    finally:
        shutil.rmtree(project_dir, ignore_errors=True)
