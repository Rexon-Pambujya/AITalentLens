"""
Storage abstraction (section 5/54: local dev uses disk/MinIO, production
targets S3-compatible storage - callers never know which).
"""
from abc import ABC, abstractmethod


class StorageBackend(ABC):
    @abstractmethod
    async def save(self, *, key: str, content: bytes, content_type: str) -> str:
        """Persists `content` under `key` and returns the storage_path to
        record on the Resume row."""

    @abstractmethod
    async def read(self, storage_path: str) -> bytes:
        """Returns raw bytes for a previously-saved object."""

    @abstractmethod
    async def delete(self, storage_path: str) -> None:
        """Removes an object. Must not raise if it's already gone (idempotent),
        so privacy-deletion flows (section 63) can always call this safely."""

    @abstractmethod
    def build_key(self, *, organization_id: str, candidate_id: str, file_name: str) -> str:
        """Builds a collision-resistant, tenant-namespaced storage key."""
