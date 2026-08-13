"""Hashing helpers used for duplicate detection (section 20)."""
import hashlib
import re


def sha256_bytes(content: bytes) -> str:
    """Exact-file duplicate detection: two byte-identical uploads (even
    re-named) hash the same."""
    return hashlib.sha256(content).hexdigest()


def normalized_text_hash(text: str) -> str:
    """Near-duplicate detection: catches the same resume re-exported to a
    different file format (PDF vs DOCX) or with trivial whitespace/casing
    differences, where the raw file hash would differ but the content is
    the same."""
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
