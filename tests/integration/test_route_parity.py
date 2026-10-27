"""Test that /extract and /api/v1/extract return identical responses for a valid PDF.

We generate a simple PDF in memory using pypdf and POST it to both routes.
"""

from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter

from app.main import app

client = TestClient(app)


def _make_pdf_bytes() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    stream = BytesIO()
    writer.write(stream)
    return stream.getvalue()

@pytest.fixture(scope="module")
def pdf_bytes():
    return _make_pdf_bytes()


def _post_extract(url: str, pdf_bytes: bytes):
    return client.post(
        url,
        data=pdf_bytes,
        headers={"Content-Type": "application/pdf"},
    )

def test_extract_routes_parity(pdf_bytes):
    resp_root = _post_extract("/extract", pdf_bytes)
    resp_v1 = _post_extract("/api/v1/extract", pdf_bytes)

    assert resp_root.status_code == 200
    assert resp_v1.status_code == 200
    json_root = resp_root.json()
    json_v1 = resp_v1.json()
    assert json_root == json_v1
