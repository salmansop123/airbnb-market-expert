import logging
from pathlib import Path

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

LOCAL_UPLOAD_DIR = Path("/tmp/stayprice_uploads")


def _s3_client():
    kwargs = {
        "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
        "region_name": settings.AWS_REGION,
        "config": Config(signature_version="s3v4"),
    }
    if settings.S3_ENDPOINT_URL:
        kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL
    return boto3.client("s3", **kwargs)


async def upload_file(key: str, content: bytes, content_type: str) -> str:
    """Upload to S3/MinIO; fall back to local filesystem for development."""
    try:
        client = _s3_client()
        client.put_object(
            Bucket=settings.S3_BUCKET,
            Key=key,
            Body=content,
            ContentType=content_type,
        )
        return f"{settings.S3_PUBLIC_BASE_URL.rstrip('/')}/{key}"
    except Exception as exc:
        logger.warning("S3 upload failed (%s); using local storage", exc)
        path = LOCAL_UPLOAD_DIR / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return f"/local-uploads/{key}"


async def delete_object(key: str) -> None:
    try:
        _s3_client().delete_object(Bucket=settings.S3_BUCKET, Key=key)
    except ClientError:
        pass
    local = LOCAL_UPLOAD_DIR / key
    if local.exists():
        local.unlink()
