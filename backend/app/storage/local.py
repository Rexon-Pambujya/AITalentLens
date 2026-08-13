import uuid
from pathlib import Path

import aiofiles

from app.storage.base import StorageBackend


class LocalStorageBackend(StorageBackend):
    """Writes resumes to disk under LOCAL_STORAGE_PATH. Fine for local dev
    and for this sandbox's verification; production should use
    S3StorageBackend (see app/storage/s3.py) via STORAGE_BACKEND=s3."""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def build_key(self, *, organization_id: str, candidate_id: str, file_name: str) -> str:
        # Never trust the client-supplied file name for the on-disk path -
        # collapse it to a random, extension-preserving name (section 32:
        # "Secure file names").
        suffix = Path(file_name).suffix.lower()
        safe_name = f"{uuid.uuid4().hex}{suffix}"
        return f"{organization_id}/{candidate_id}/{safe_name}"

    async def save(self, *, key: str, content: bytes, content_type: str) -> str:
        full_path = self.base_path / key
        full_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(full_path, "wb") as f:
            await f.write(content)
        return str(key)

    async def read(self, storage_path: str) -> bytes:
        full_path = self.base_path / storage_path
        async with aiofiles.open(full_path, "rb") as f:
            return await f.read()

    async def delete(self, storage_path: str) -> None:
        full_path = self.base_path / storage_path
        full_path.unlink(missing_ok=True)
