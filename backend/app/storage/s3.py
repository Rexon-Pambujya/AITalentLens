import uuid
from pathlib import Path

import boto3
from botocore.client import Config as BotoConfig
from botocore.exceptions import ClientError

from app.core.config import get_settings
from app.storage.base import StorageBackend

settings = get_settings()


class S3StorageBackend(StorageBackend):
    """S3-compatible backend. Works unmodified against real AWS S3 or
    against MinIO locally by pointing S3_ENDPOINT at the MinIO container
    (see infra/docker-compose.yml) - same code path in both environments,
    which is the point of the abstraction (section 4: Object Storage)."""

    def __init__(self):
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,  # None -> real AWS
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
            # path-style addressing: required by Cloudflare R2 (the free-tier
            # deploy target); also works fine against MinIO/real AWS.
            config=BotoConfig(signature_version="s3v4", s3={"addressing_style": "path"}),
        )
        self._bucket = settings.S3_BUCKET

    def build_key(self, *, organization_id: str, candidate_id: str, file_name: str) -> str:
        suffix = Path(file_name).suffix.lower()
        safe_name = f"{uuid.uuid4().hex}{suffix}"
        return f"{organization_id}/{candidate_id}/{safe_name}"

    async def save(self, *, key: str, content: bytes, content_type: str) -> str:
        self._client.put_object(Bucket=self._bucket, Key=key, Body=content, ContentType=content_type)
        return key

    async def read(self, storage_path: str) -> bytes:
        response = self._client.get_object(Bucket=self._bucket, Key=storage_path)
        return response["Body"].read()

    async def delete(self, storage_path: str) -> None:
        try:
            self._client.delete_object(Bucket=self._bucket, Key=storage_path)
        except ClientError:
            pass  # already gone - deletion must be idempotent (section 63)
