"""PDF text extraction (section 7: PyMuPDF/fitz)."""
import fitz  # PyMuPDF

from app.core.exceptions import UnsupportedDocumentError


def extract_text_from_pdf(content: bytes) -> str:
    """Extracts text page-by-page. Raises UnsupportedDocumentError for
    corrupt/unreadable PDFs rather than letting a low-level fitz exception
    surface as a 500 (section 39: no raw stack traces to the client)."""
    try:
        doc = fitz.open(stream=content, filetype="pdf")
    except Exception as exc:
        raise UnsupportedDocumentError("Could not open PDF - file may be corrupt") from exc

    if doc.page_count == 0:
        raise UnsupportedDocumentError("PDF contains no pages")

    pages: list[str] = []
    for page in doc:
        pages.append(page.get_text("text"))
    doc.close()

    text = "\n".join(pages).strip()
    if not text:
        # A scanned/image-only PDF with no extractable text layer. The
        # pipeline should not crash - OCR is a pluggable fallback
        # (section 7 / app/ingestion/ocr.py); for now we surface this
        # clearly so the caller can mark the resume as needing OCR.
        raise UnsupportedDocumentError(
            "No extractable text found in PDF - it may be a scanned image without OCR"
        )
    return text
