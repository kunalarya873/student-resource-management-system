import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import aioboto3
from botocore.config import Config
from botocore.exceptions import ClientError
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger("amu_storage")


class StorageService:
    """Asynchronous S3 / MinIO Object Storage Service."""

    def __init__(self) -> None:
        self.session = aioboto3.Session()
        self.boto_config = Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            retries={"max_attempts": 3, "mode": "standard"},
        )

    @asynccontextmanager
    async def get_client(self) -> AsyncGenerator:
        """Yield an authenticated async aioboto3 S3 client."""
        async with self.session.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            region_name=settings.S3_REGION,
            config=self.boto_config,
        ) as client:
            yield client

    async def ensure_bucket_exists(self) -> None:
        """Ensure the target academic resources bucket exists in S3/MinIO."""
        async with self.get_client() as s3:
            try:
                await s3.head_bucket(Bucket=settings.S3_BUCKET_NAME)
            except ClientError as exc:
                error_code = exc.response.get("Error", {}).get("Code")
                if error_code in ("404", "NoSuchBucket"):
                    logger.info("Bucket %s not found. Creating...", settings.S3_BUCKET_NAME)
                    await s3.create_bucket(Bucket=settings.S3_BUCKET_NAME)
                else:
                    logger.error("Failed to inspect bucket %s: %s", settings.S3_BUCKET_NAME, exc)
                    raise

    async def generate_presigned_upload_url(
        self,
        object_key: str,
        content_type: str,
        expires_in: int = 1800,
    ) -> str:
        """Generate a presigned PUT URL for direct client-to-storage upload."""
        async with self.get_client() as s3:
            try:
                url = await s3.generate_presigned_url(
                    ClientMethod="put_object",
                    Params={
                        "Bucket": settings.S3_BUCKET_NAME,
                        "Key": object_key,
                        "ContentType": content_type,
                    },
                    ExpiresIn=expires_in,
                )
                return url
            except Exception as exc:
                logger.error("Failed to generate presigned upload URL: %s", exc)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate secure upload credentials.",
                ) from exc

    async def generate_presigned_download_url(
        self,
        object_key: str,
        filename: str,
        expires_in: int = 300,
    ) -> str:
        """Generate a presigned GET URL for secure downloading with Content-Disposition."""
        async with self.get_client() as s3:
            try:
                url = await s3.generate_presigned_url(
                    ClientMethod="get_object",
                    Params={
                        "Bucket": settings.S3_BUCKET_NAME,
                        "Key": object_key,
                        "ResponseContentDisposition": f'attachment; filename="{filename}"',
                    },
                    ExpiresIn=expires_in,
                )
                return url
            except Exception as exc:
                logger.error("Failed to generate presigned download URL: %s", exc)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate secure download URL.",
                ) from exc

    async def verify_uploaded_object(self, object_key: str) -> tuple[bool, int, str]:
        """Verify presence, length, and ETag of an object in MinIO/S3 via HeadObject."""
        async with self.get_client() as s3:
            try:
                response = await s3.head_object(Bucket=settings.S3_BUCKET_NAME, Key=object_key)
                content_length = int(response.get("ContentLength", 0))
                etag = str(response.get("ETag", "")).strip('"')
                return True, content_length, etag
            except ClientError as exc:
                error_code = exc.response.get("Error", {}).get("Code")
                if error_code in ("404", "NoSuchKey", "NotFound"):
                    return False, 0, ""
                logger.warning("Error checking object %s: %s", object_key, exc)
                return False, 0, ""
            except Exception as exc:  # noqa: BLE001
                logger.warning("Unexpected error checking object %s: %s", object_key, exc)
                return False, 0, ""

    async def delete_object(self, object_key: str) -> bool:
        """Remove an object from storage."""
        async with self.get_client() as s3:
            try:
                await s3.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=object_key)
                return True
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to delete object %s: %s", object_key, exc)
                return False


storage_service = StorageService()
