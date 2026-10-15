"""Integration tests for API endpoints - Task 5."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


def test_extract_endpoint_valid_payload():
    """POST /api/v1/extract with valid multipart payload returns 200 and extracted text."""
    from app.dtos.extraction import ExtractResponse

    client = TestClient(app)

    pdf_bytes = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >
endobj
xref
0 2
0000000000 65535 f 
0000000009 00000 n 
trailer
<< /Size 2 /Root 1 0 R >
startxref
9
%%EOF"""

    with patch("app.api.v1.endpoints.extract_pdf_text") as mock_extract:
        mock_extract.return_value = ExtractResponse(
            content="# Extracted Text", page_count=1
        )
        response = client.post(
            "/api/v1/extract",
            files={"file": ("prueba.pdf", pdf_bytes, "application/pdf")},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["content"] == "# Extracted Text"
        assert body["page_count"] == 1


def test_extract_endpoint_invalid_base64():
    """POST /api/v1/extract with invalid input returns 400 Problem Details (RFC 9457)."""
    client = TestClient(app)

    # Enviar archivo vacío o datos inválidos
    response = client.post(
        "/api/v1/extract",
        files={"file": ("test.pdf", b"not a pdf", "application/pdf")},
    )
    # Debe retornar error (400 o 422) con formato Problem Details
    assert response.status_code in (400, 422)
    body = response.json()
    # RFC 9457 Problem Details required fields
    assert "type" in body
    assert "title" in body
    assert "status" in body
    assert "detail" in body


def test_extract_endpoint_invalid_pdf():
    """POST /api/v1/extract with corrupt PDF returns error."""
    client = TestClient(app)

    response = client.post(
        "/api/v1/extract",
        files={"file": ("corrupt.pdf", b"%%% CORRUPT %%%", "application/pdf")},
    )
    # Should return some error (400 or 422) with Problem Details format
    assert response.status_code in (400, 422)
    if response.status_code in (400, 422):
        body = response.json()
        assert "type" in body or "detail" in body


def test_health_endpoint():
    """GET /health returns 200 with health status."""
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok" or "status" in body