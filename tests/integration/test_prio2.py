"""Prioridad 2: RFC 9457 422/413, X-Request-ID and JSON logs without PDF content."""

import json
import logging
import os
import re
from unittest.mock import patch

import pymupdf
import pytest
from fastapi.testclient import TestClient

from app.api.v1 import endpoints
from app.core.observability import JsonFormatter
from app.infrastructure.pdf_reader import InfraExtractionError, extract_text
from app.main import app
from app.services import cache

PDF_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "stress", "pdfs", "Filosofia_Lean.pdf")
)


@pytest.fixture
def client():
    cache.clear()
    return TestClient(app)


def _real_pdf() -> bytes:
    with open(PDF_PATH, "rb") as f:
        return f.read()


def _encrypted_pdf() -> bytes:
    doc = pymupdf.open()
    doc.new_page()
    data = doc.tobytes(
        encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="secreto", owner_pw="duenio"
    )
    doc.close()
    return data


# --- E-03: 422 for corrupt / password-protected PDFs --------------------------------

def test_encrypted_pdf_raises_kind_encrypted():
    with pytest.raises(InfraExtractionError) as exc:
        extract_text(_encrypted_pdf())
    assert exc.value.kind == "encrypted"


def test_unreadable_pdf_raises_kind_corrupt():
    with pytest.raises(InfraExtractionError) as exc:
        extract_text(b"not a pdf at all")
    assert exc.value.kind == "corrupt"


def test_encrypted_pdf_returns_422_problem_details(client):
    resp = client.post(
        "/extract", files={"file": ("enc.pdf", _encrypted_pdf(), "application/pdf")}
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["status"] == 422
    assert body["title"] == "Unprocessable Entity"
    assert body["detail"] == "PDF is password-protected"


def test_corrupt_pdf_returns_422_problem_details(client):
    error = InfraExtractionError("boom", kind="corrupt")
    with patch("app.services.extraction.extract_text", side_effect=error):
        resp = client.post(
            "/extract", files={"file": ("bad.pdf", b"%PDF-1.4 truncated", "application/pdf")}
        )
    assert resp.status_code == 422
    assert resp.json()["detail"] == "PDF is corrupt or unreadable"


# --- PDF_MAX_FILE_SIZE_MB: 413 ---------------------------------------------------------

def test_pdf_over_max_size_returns_413(client, monkeypatch):
    monkeypatch.setattr(endpoints.settings, "PDF_MAX_FILE_SIZE_MB", 0)
    resp = client.post(
        "/extract", files={"file": ("a.pdf", _real_pdf(), "application/pdf")}
    )
    assert resp.status_code == 413
    assert resp.json()["status"] == 413
    assert resp.json()["title"] == "Payload Too Large"


# --- E-06: X-Request-ID and JSON logs ------------------------------------------------

def test_valid_request_id_is_echoed(client):
    resp = client.get("/health", headers={"X-Request-ID": "req-abc_123.4"})
    assert resp.headers["x-request-id"] == "req-abc_123.4"


def test_request_id_is_generated_when_missing_or_invalid(client):
    resp = client.get("/health")
    assert re.fullmatch(r"[0-9a-f]{32}", resp.headers["x-request-id"])

    too_long = "x" * 200
    resp = client.get("/health", headers={"X-Request-ID": too_long})
    assert resp.headers["x-request-id"] != too_long
    assert re.fullmatch(r"[0-9a-f]{32}", resp.headers["x-request-id"])


def test_access_log_is_json_with_request_id_and_no_pdf_content(client, caplog):
    caplog.set_level(logging.INFO)
    resp = client.post(
        "/extract",
        files={"file": ("doc.pdf", _real_pdf(), "application/pdf")},
        headers={"X-Request-ID": "trace-1"},
    )
    assert resp.status_code == 200

    records = [
        r for r in caplog.records
        if r.name == "access" and getattr(r, "request_id", None) == "trace-1"
    ]
    assert len(records) == 1
    record = records[0]
    assert record.method == "POST"
    assert record.path == "/extract"
    assert record.status == 200

    line = JsonFormatter().format(record)
    payload = json.loads(line)
    assert payload["request_id"] == "trace-1"
    assert payload["duration_ms"] >= 0
    assert "%PDF" not in line
    assert "content" not in payload
