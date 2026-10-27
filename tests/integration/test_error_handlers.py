import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_extract_invalid_content_type_returns_rfc9457():
    """Send POST /extract with unsupported Content-Type and verify RFC 9457 response."""
    response = client.post(
        "/extract",
        data="hola",
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 415
    # The handler should return a JSON body with RFC 9457 fields
    body = response.json()
    for key in ["type", "title", "status", "detail", "instance"]:
        assert key in body
    assert body["status"] == 415
    assert body["instance"] == "/extract"

def test_extract_missing_content_type_returns_rfc9457():
    """Send POST /extract without Content-Type header and verify RFC 9457 response."""
    response = client.post("/extract", data="hola")
    # FastAPI will respond with 415 for unsupported media type, but could be 400 for validation
    assert response.status_code in (415, 400)
    body = response.json()
    for key in ["type", "title", "status", "detail", "instance"]:
        assert key in body
    assert body["status"] == response.status_code
    assert body["instance"] == "/extract"
