"""Unit tests for DTOs - Task 2."""


def test_extract_request_importable():
    """Test that dtos.extraction.ExtractRequest is importable."""
    from app.dtos.extraction import ExtractRequest

    r = ExtractRequest(base64_pdf="dummy_payload")
    assert r.base64_pdf == "dummy_payload"


def test_extract_response_importable():
    """Test that dtos.extraction.ExtractResponse is importable."""
    from app.dtos.extraction import ExtractResponse

    r = ExtractResponse(extracted_text="some text", status="ok")
    assert r.extracted_text == "some text"
    assert r.status == "ok"


def test_extract_request_and_response_json():
    """Test that DTOs can be serialized/deserialized to/from JSON."""
    import json

    from app.dtos.extraction import ExtractRequest, ExtractResponse

    req = ExtractRequest(base64_pdf="base64pdfdata")
    req_json = req.model_dump_json()
    parsed = json.loads(req_json)
    assert parsed["base64_pdf"] == "base64pdfdata"

    resp = ExtractResponse(extracted_text="Hello World", status="success")
    resp_json = resp.model_dump_json()
    parsed_resp = json.loads(resp_json)
    assert parsed_resp["extracted_text"] == "Hello World"
    assert parsed_resp["status"] == "success"
