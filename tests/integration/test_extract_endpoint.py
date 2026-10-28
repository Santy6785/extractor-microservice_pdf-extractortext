import pytest
import httpx
from httpx import AsyncClient
import pymupdf
from app.main import app


@pytest.mark.asyncio
async def test_extract_endpoint_multipart_success(tmp_path):
    # Create a simple PDF in memory using pymupdf
    pdf_path = tmp_path / "sample.pdf"
    doc = pymupdf.open()
    doc.new_page(width=72, height=72)
    doc.save(str(pdf_path))
    doc.close()

    async with AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
        with open(pdf_path, "rb") as f:
            files = {"file": ("sample.pdf", f, "application/pdf")}
            response = await client.post("/extract", files=files)
    assert response.status_code == 200, response.text
    json = response.json()
    assert "content" in json and isinstance(json["content"], str)
    assert "page_count" in json and isinstance(json["page_count"], int)
