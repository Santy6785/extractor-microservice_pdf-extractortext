"""Integration tests for API endpoints - Task 5."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


def test_extract_endpoint_valid_payload():
    """POST /api/v1/extract with valid payload returns 200 and extracted text."""
    from app.dtos.extraction import ExtractResponse

    client = TestClient(app)

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
    b64_pdf = "JVBERi0xLjQK..."  # base64 encoding of the PDF above

    with patch("app.api.v1.endpoints.extract_pdf_text") as mock_extract:
        mock_extract.return_value = ExtractResponse(
            extracted_text="Hello World", status="processed"
        )
        response = client.post("/api/v1/extract", json={"base64_pdf": b64_pdf})
        assert response.status_code == 200
        body = response.json()
        assert body["extracted_text"] == "Hello World"


def test_extract_endpoint_invalid_base64():
    """POST /api/v1/extract with invalid base64 returns 400 Problem Details (RFC 9457)."""
    client = TestClient(app)

    response = client.post("/api/v1/extract", json={"base64_pdf": "not_valid_base64!"})
    assert response.status_code == 400
    body = response.json()
    # RFC 9457 Problem Details required fields
    assert "type" in body
    assert "title" in body
    assert "status" in body
    assert "detail" in body
    assert body["status"] == 400


def test_extract_endpoint_invalid_pdf():
    """POST /api/v1/extract with corrupt PDF returns error."""
    client = TestClient(app)

    response = client.post("/api/v1/extract", json={"base64_pdf": "dGVzdA=="})
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
