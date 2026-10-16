import logging
import mimetypes
import os
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from django.conf import settings

logger = logging.getLogger(__name__)


class ObjectNotFound(Exception):
    pass


@lru_cache(maxsize=1)
def get_s3():
    return boto3.client(
        "s3",
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        endpoint_url=settings.R2_ENDPOINT_URL,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )


def upload_file(key: str, local_path) -> None:
    content_type = (
        mimetypes.guess_type(str(local_path))[0] or "application/octet-stream"
    )
    get_s3().upload_file(
        str(local_path),
        settings.R2_BUCKET,
        key,
        ExtraArgs={"ContentType": content_type},
    )


def upload_folder(local_folder, key_prefix: str, skip_dirs=(), workers: int = 8) -> int:
    """Upload every file under local_folder to `<key_prefix>/<relative path>`.

    Blocks until all uploads finish and raises if any fail. Returns the file count.
    """
    local_folder = Path(local_folder)
    jobs = []
    for root, dirs, files in os.walk(local_folder):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for name in files:
            full = Path(root) / name
            rel = full.relative_to(local_folder).as_posix()
            jobs.append((f"{key_prefix.rstrip('/')}/{rel}", full))

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(upload_file, key, path) for key, path in jobs]
        for f in futures:
            f.result()  # propagate errors
    return len(jobs)


def download_prefix(prefix: str, dest_root) -> int:
    """Download every object under `prefix` to `dest_root/<key>`. Returns the file count."""
    dest_root = Path(dest_root).resolve()
    paginator = get_s3().get_paginator("list_objects_v2")
    count = 0
    for page in paginator.paginate(Bucket=settings.R2_BUCKET, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith("/"):
                continue
            target = (dest_root / key).resolve()
            if dest_root not in target.parents:
                raise ValueError(f"Refusing to write outside work dir: {key}")
            target.parent.mkdir(parents=True, exist_ok=True)
            get_s3().download_file(settings.R2_BUCKET, key, str(target))
            count += 1
    return count


def get_object(key: str) -> dict:
    try:
        return get_s3().get_object(Bucket=settings.R2_BUCKET, Key=key)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in ("NoSuchKey", "404", "NotFound"):
            raise ObjectNotFound(key) from exc
        raise
