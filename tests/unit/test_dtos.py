"""Unit tests for DTOs - Task 2."""

import json


def test_extract_request_importable():
    """Test that dtos.extraction.ExtractRequest is importable."""
    from app.dtos.extraction import ExtractRequest

    r = ExtractRequest(file=b"dummy_payload")
    assert r.file == b"dummy_payload"


def test_extract_response_importable():
    """Test that dtos.extraction.ExtractResponse is importable."""
    from app.dtos.extraction import ExtractResponse

    r = ExtractResponse(content="some text", page_count=1)
    assert r.content == "some text"
    assert r.page_count == 1


def test_extract_request_and_response_json():
    """Test that DTOs can be serialized/deserialized to/from JSON."""
    from app.dtos.extraction import ExtractRequest, ExtractResponse

    req = ExtractRequest(file=b"base64pdfdata")
    req_json = req.model_dump_json()
    parsed = json.loads(req_json)
    assert parsed["file"].startswith("base64pdfdata")

    resp = ExtractResponse(content="Hello World", page_count=1)
    resp_json = resp.model_dump_json()
    parsed_resp = json.loads(resp_json)
    assert parsed_resp["content"] == "Hello World"
    assert parsed_resp["page_count"] == 1