"""Unit tests for extraction service - Task 4."""

import base64
from unittest.mock import patch

import pytest


def test_extract_service_importable():
    """Test that services.extraction.extract_pdf_text is importable."""
    from app.services.extraction import extract_pdf_text

    assert callable(extract_pdf_text)


def test_extract_service_valid_base64():
    """Test that extract_pdf_text processes valid base64 PDF correctly.

    With mock infrastructure, should return ExtractResponse with extracted text.
    """
    from app.dtos.extraction import ExtractResponse
    from app.services.extraction import extract_pdf_text

    # Create a simple valid PDF and base64-encode it
    pdf_bytes = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
xref
0 2
0000000000 65535 f 
0000000009 00000 n 
trailer
<< /Size 2 /Root 1 0 R >>
startxref
9
%%EOF"""
    b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")

    # Test with mock that returns extracted text
    with patch("app.services.extraction.extract_text") as mock_extract:
        mock_extract.return_value = "Extracted text from page 1"
        result: ExtractResponse = extract_pdf_text(b64_pdf)
        assert result.extracted_text == "Extracted text from page 1"
        assert result.status == "processed"


def test_extract_service_invalid_base64_returns_infra_error():
    """Test that invalid base64 raises InfraExtractionError.

    Verifies the service layer catches base64 decode errors and wraps
    them as infrastructure errors (RFC 9457 mapping happens at API layer).
    """
    from app.infrastructure.pdf_reader import InfraExtractionError
    from app.services.extraction import extract_pdf_text

    # Invalid base64 should raise InfraExtractionError from the service
    with pytest.raises(InfraExtractionError) as exc_info:
        extract_pdf_text("not_valid_base64!")
    assert "Invalid base64" in str(exc_info.value)


def test_extract_service_extract_text_error():
    """Test that extraction errors from infra are propagated.

    Tests that when the infrastructure adapter fails, the service
    propagates the InfraExtractionError.
    """
    from app.infrastructure.pdf_reader import InfraExtractionError
    from app.services.extraction import extract_pdf_text

    pdf_bytes = b"%PDF-1.4 fake content"
    b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")

    with patch("app.services.extraction.extract_text") as mock_extract:
        mock_extract.side_effect = InfraExtractionError("PDF read error")
        with pytest.raises(InfraExtractionError) as exc_info:
            extract_pdf_text(b64_pdf)
        assert "PDF read error" in str(exc_info.value)


def test_extract_service_no_fastapi_import():
    """Test that the service module does not import FastAPI or HTTP types.

    Ensures the architecture boundary is maintained.
    """
    import pathlib

    source = pathlib.Path("app/services/extraction.py").read_text()
    # Should not contain "from fastapi" or "from starlette" or "import HTTPException"
    assert "from fastapi" not in source, "Service layer must not import FastAPI"
    assert "from starlette" not in source, "Service layer must not import Starlette"
    assert "HTTPException" not in source, "Service layer must not import HTTPException"


def test_extract_service_returns_dto():
    """Test that the service returns an ExtractResponse DTO.

    Verifies the return type and that required fields are present.
    """
    from app.dtos.extraction import ExtractResponse
    from app.services.extraction import extract_pdf_text

    # Create a valid base64 PDF
    pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\nxref\n0 2\n0000000000 65535 f \n0000000009 00000 n \ntrailer\n<< /Size 2 /Root 1 0 R >>\nstartxref\n9\n%%EOF"
    b64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")

    # With mock that returns text
    with patch("app.services.extraction.extract_text") as mock_extract:
        mock_extract.return_value = "Hello World"
        result = extract_pdf_text(b64_pdf)
        assert isinstance(result, ExtractResponse)
        assert hasattr(result, "extracted_text")
        assert hasattr(result, "status")
