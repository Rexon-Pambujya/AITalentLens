"""
Pluggable OCR abstraction (section 7). Only invoked when PDF/DOCX text
extraction comes back empty (i.e. a scanned/image-only document).

This ships a Tesseract-backed implementation behind a capability check so
the pipeline degrades gracefully (section 62) on hosts without the
`tesseract` binary installed, rather than crashing the whole upload.
"""
import io
import shutil
from abc import ABC, abstractmethod

from app.core.logging import get_logger

logger = get_logger(__name__)


class OCRProvider(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        ...

    @abstractmethod
    def extract_text(self, image_bytes: bytes) -> str:
        ...


class TesseractOCRProvider(OCRProvider):
    def is_available(self) -> bool:
        return shutil.which("tesseract") is not None

    def extract_text(self, image_bytes: bytes) -> str:
        import pytesseract
        from PIL import Image

        image = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(image)


def get_ocr_provider() -> OCRProvider | None:
    provider = TesseractOCRProvider()
    if not provider.is_available():
        logger.warning("ocr_unavailable", reason="tesseract binary not found on PATH")
        return None
    return provider
