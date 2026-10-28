"""Unit tests for infrastructure layer using pymupdf - Task 5b."""

from unittest.mock import patch

import pytest
import pymupdf

from app.infrastructure.pdf_reader import InfraExtractionError, extract_text


def test_pdf_reader_importable():
    """Test that infra.pdf_reader.extract_text is importable."""
    assert callable(extract_text)


def test_pdf_reader_raises_on_invalid():
    """Test that extract_text raises InfraExtractionError on invalid input."""
    with pytest.raises(InfraExtractionError):
        extract_text(b"not a pdf at all")


def test_pdf_reader_empty_bytes():
    """Test that extract_text raises InfraExtractionError on empty bytes."""
    with pytest.raises(InfraExtractionError) as excinfo:
        extract_text(b"")
    assert "PDF bytes are empty" in str(excinfo.value)


def test_pdf_reader_extracts_text_real_pdf():
    """Test extract_text success path with a real PDF generated via pymupdf."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), "Extracted page text")
    pdf_bytes = doc.tobytes()
    doc.close()

    raw_text, page_count = extract_text(pdf_bytes)
    assert isinstance(raw_text, str)
    assert "Extracted page text" in raw_text
    assert page_count == 1


def test_pdf_reader_no_text_page():
    """Test extract_text when PDF pages contain no text."""
    doc = pymupdf.open()
    doc.new_page()
    pdf_bytes = doc.tobytes()
    doc.close()

    raw_text, page_count = extract_text(pdf_bytes)
    assert raw_text == ""
    assert page_count == 1


def test_pdf_reader_multiple_pages():
    """Test extract_text with multiple pages."""
    doc = pymupdf.open()
    page1 = doc.new_page()
    page1.insert_text((50, 72), "Page 1 content")
    page2 = doc.new_page()
    page2.insert_text((50, 72), "Page 2 content")
    pdf_bytes = doc.tobytes()
    doc.close()

    raw_text, page_count = extract_text(pdf_bytes)
    assert "Page 1 content" in raw_text
    assert "Page 2 content" in raw_text
    assert page_count == 2


def test_pdf_reader_unexpected_error():
    """Test extract_text handles unexpected exceptions in pymupdf."""
    with patch("app.infrastructure.pdf_reader.pymupdf.open", side_effect=RuntimeError("Internal parsing error")):
        with pytest.raises(InfraExtractionError) as excinfo:
            extract_text(b"%PDF-1.4 dummy")
        assert "Failed to extract PDF text" in str(excinfo.value)
