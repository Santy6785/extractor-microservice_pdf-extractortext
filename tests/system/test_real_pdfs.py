import os
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.extraction import extract_pdf_text

pdf_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "stress", "pdfs"))

EXPECTED_PAGE_COUNTS = {
    "2020-Scrum-Guide-Spanish-Latin-South-American.pdf": 16,
    "scrum_manager_historias_usuario.pdf": 62,
    "Essential-Kanban-Condensed-Spanish.pdf": 90,
    "Filosofia_Lean.pdf": 42,
}

exists = all(os.path.isfile(os.path.join(pdf_dir, f)) for f in EXPECTED_PAGE_COUNTS)


@pytest.mark.skipif(not exists, reason="PDF test files not present")
@pytest.mark.asyncio
async def test_real_pdfs_extraction():
    """Verify endpoint extraction of all 4 real PDFs with expected page counts and non-empty content."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        for pdf_name, expected_pages in EXPECTED_PAGE_COUNTS.items():
            path = os.path.join(pdf_dir, pdf_name)
            with open(path, "rb") as f:
                pdf_bytes = f.read()

            response = await client.post(
                "/extract",
                files={"file": (pdf_name, pdf_bytes, "application/pdf")},
            )
            assert response.status_code == 200, f"Extraction failed for {pdf_name}: {response.text}"
            data = response.json()
            assert data.get("page_count") == expected_pages, (
                f"{pdf_name}: expected {expected_pages} pages, got {data.get('page_count')}"
            )
            content = data.get("content")
            assert isinstance(content, str) and content.strip() != "", f"{pdf_name}: empty content"
            assert not content.lstrip().startswith(">")


@pytest.mark.skipif(not exists, reason="PDF test files not present")
def test_real_pdfs_service_direct():
    """Verify direct service extraction of all 4 real PDFs without mocks."""
    for pdf_name, expected_pages in EXPECTED_PAGE_COUNTS.items():
        path = os.path.join(pdf_dir, pdf_name)
        with open(path, "rb") as f:
            pdf_bytes = f.read()

        result = extract_pdf_text(pdf_bytes)
        assert result.page_count == expected_pages, (
            f"{pdf_name}: expected {expected_pages} pages, got {result.page_count}"
        )
        assert isinstance(result.content, str) and result.content.strip() != "", (
            f"{pdf_name}: empty content in service response"
        )
