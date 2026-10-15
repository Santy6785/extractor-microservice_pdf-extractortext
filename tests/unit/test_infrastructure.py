"""Unit tests for infrastructure layer - Task 3."""

from unittest.mock import MagicMock, patch

import pytest

from app.infrastructure.pdf_reader import InfraExtractionError, extract_text


def test_pdf_reader_importable():
    """Test that infra.pdf_reader.extract_text is importable."""
    from app.infrastructure.pdf_reader import InfraExtractionError, extract_text

    # With invalid content, pypdf raises PdfStreamError which wraps to InfraExtractionError
    pdf_bytes = b"%PDF-1.4 fake content"
    with pytest.raises(InfraExtractionError):
        extract_text(pdf_bytes)


def test_pdf_reader_raises_on_invalid():
    """Test that extract_text raises InfraExtractionError on invalid input."""
    from app.infrastructure.pdf_reader import InfraExtractionError, extract_text

    with pytest.raises(InfraExtractionError):
        extract_text(b"not a pdf at all")


def test_pdf_reader_empty_bytes():
    """Test that extract_text raises InfraExtractionError on empty bytes."""
    with pytest.raises(InfraExtractionError) as excinfo:
        extract_text(b"")
    assert "PDF bytes are empty" in str(excinfo.value)


def test_pdf_reader_with_mocked_success():
    """Test extract_text success path with mocked PdfReader.

    Covers the try block (text extraction logic) and
    verifies the return value when text is successfully extracted.
    The function returns a tuple (markdown_text, page_count).
    """
    from app.infrastructure.pdf_reader import extract_text

    # Create a mock page object that returns text when extract_text is called
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Extracted page text"

    # Create a mock reader with pages that have text
    mock_reader = MagicMock()
    mock_reader.pages = [mock_page]

    with patch("app.infrastructure.pdf_reader.PdfReader", return_value=mock_reader):
        result = extract_text(b"any pdf bytes")
        assert isinstance(result, tuple)
        markdown, page_count = result
        assert "# PDF Extraction" in markdown
        assert page_count == 1


def test_pdf_reader_with_mocked_no_text():
    """Test extract_text returns markdown with page count when PDF has no extractable text."""
    from app.infrastructure.pdf_reader import extract_text

    # Create a mock page object that returns None/empty text
    mock_page = MagicMock()
    mock_page.extract_text.return_value = None

    # Create a mock reader with pages
    mock_reader = MagicMock()
    mock_reader.pages = [mock_page]

    with patch("app.infrastructure.pdf_reader.PdfReader", return_value=mock_reader):
        result = extract_text(b"any pdf bytes")
        assert isinstance(result, tuple)
        markdown, page_count = result
        assert page_count == 1
        assert "*No text extracted*" in markdown


def test_pdf_reader_with_mocked_empty_pages():
    """Test extract_text with empty pages list.

    Covers the case when reader.pages is an empty list,
    resulting in text_parts being empty and returning markdown with page_count=0.
    """
    from app.infrastructure.pdf_reader import extract_text

    # Create a mock reader with no pages
    mock_reader = MagicMock()
    mock_reader.pages = []

    with patch("app.infrastructure.pdf_reader.PdfReader", return_value=mock_reader):
        result = extract_text(b"any pdf bytes")
        assert isinstance(result, tuple)
        markdown, page_count = result
        assert page_count == 0
        assert "*No text extracted*" in markdown


def test_pdf_reader_unexpected_error():
    """Test extract_text handles unexpected exceptions (general Exception handler).

    This covers lines 49-50 the general Exception catch-all branch.
    We mock PdfReader to raise a non-PdfReadError exception.
    """
    from app.infrastructure.pdf_reader import InfraExtractionError, extract_text

    # Make PdfReader raise a ValueError (not PdfReadError)
    # This should be caught by the general Exception handler on lines 49-50
    with patch(
        "app.infrastructure.pdf_reader.PdfReader",
        side_effect=ValueError("Unexpected error"),
    ):
        with pytest.raises(InfraExtractionError) as excinfo:
            extract_text(b"any pdf bytes")
        assert "Unexpected error extracting PDF text" in str(excinfo.value)