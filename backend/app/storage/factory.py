from functools import lru_cache

from app.core.config import get_settings
from app.storage.base import StorageBackend

settings = get_settings()


@lru_cache
def get_storage_backend() -> StorageBackend:
    if settings.STORAGE_BACKEND == "s3":
        from app.storage.s3 import S3StorageBackend

        return S3StorageBackend()
    from app.storage.local import LocalStorageBackend

    return LocalStorageBackend(settings.LOCAL_STORAGE_PATH)
