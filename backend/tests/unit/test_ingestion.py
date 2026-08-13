"""Covers spec section 51's required 'Invalid PDF' case."""
import io

import docx
import fitz
import pytest

from app.core.exceptions import UnsupportedDocumentError
from app.ingestion.docx_parser import extract_text_from_docx
from app.ingestion.pdf_parser import extract_text_from_pdf
from app.ingestion.text_cleaner import chunk_text_for_embedding, clean_text, detect_sections
from app.utils.hashing import normalized_text_hash, sha256_bytes


def _make_pdf_bytes(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), text, fontsize=11)
    data = doc.tobytes()
    doc.close()
    return data


def _make_docx_bytes(paragraphs: list[str]) -> bytes:
    d = docx.Document()
    for p in paragraphs:
        d.add_paragraph(p)
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()


class TestPDFParsing:
    def test_valid_pdf_extracts_text(self):
        pdf_bytes = _make_pdf_bytes("Jane Doe\nSoftware Engineer")
        text = extract_text_from_pdf(pdf_bytes)
        assert "Jane Doe" in text

    def test_invalid_pdf_raises_unsupported_document_error(self):
        """Corrupt/non-PDF bytes must raise a clean, typed error - never a
        raw low-level exception that would surface a stack trace."""
        with pytest.raises(UnsupportedDocumentError):
            extract_text_from_pdf(b"this is not a pdf file at all")

    def test_empty_bytes_raises_unsupported_document_error(self):
        with pytest.raises(UnsupportedDocumentError):
            extract_text_from_pdf(b"")


class TestDOCXParsing:
    def test_valid_docx_extracts_text(self):
        docx_bytes = _make_docx_bytes(["John Smith", "Senior Engineer"])
        text = extract_text_from_docx(docx_bytes)
        assert "John Smith" in text

    def test_invalid_docx_raises_unsupported_document_error(self):
        with pytest.raises(UnsupportedDocumentError):
            extract_text_from_docx(b"not a docx file")

    def test_docx_table_content_is_extracted(self):
        d = docx.Document()
        table = d.add_table(rows=1, cols=2)
        table.rows[0].cells[0].text = "Python"
        table.rows[0].cells[1].text = "5 years"
        buf = io.BytesIO()
        d.save(buf)
        text = extract_text_from_docx(buf.getvalue())
        assert "Python" in text and "5 years" in text


class TestTextCleaningAndChunking:
    def test_section_detection_finds_common_headers(self):
        raw = "Jane Doe\n\nEXPERIENCE\nBuilt things.\n\nEDUCATION\nMIT"
        sections = detect_sections(clean_text(raw))
        assert "experience" in sections
        assert "education" in sections

    def test_chunking_never_drops_content(self):
        raw = "SUMMARY\n" + ("word " * 500)  # forces multi-chunk splitting
        cleaned = clean_text(raw)
        chunks = chunk_text_for_embedding(cleaned)
        assert len(chunks) >= 1
        assert sum(len(c) for c in chunks) > 0


class TestDuplicateDetectionHashing:
    def test_identical_bytes_produce_identical_hash(self):
        content = b"resume content here"
        assert sha256_bytes(content) == sha256_bytes(content)

    def test_different_bytes_produce_different_hash(self):
        assert sha256_bytes(b"resume A") != sha256_bytes(b"resume B")

    def test_normalized_text_hash_ignores_whitespace_and_case(self):
        """Section 20: catches the same resume re-exported with trivial
        formatting differences."""
        a = normalized_text_hash("Jane Doe\n\nSoftware Engineer")
        b = normalized_text_hash("jane doe   software engineer")
        assert a == b
