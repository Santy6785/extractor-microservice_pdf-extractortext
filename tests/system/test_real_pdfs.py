import os
import pytest
from fastapi import UploadFile
from httpx import AsyncClient, ASGITransport
from app.main import app

pdf_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "stress", "pdfs"))
pdf_files = [
    "2020-Scrum-Guide-Spanish-Latin-South-American.pdf",
    "scrum_manager_historias_usuario.pdf",
    "Essential-Kanban-Condensed-Spanish.pdf",
    "Filosofia_Lean.pdf",
]

exists = all(os.path.isfile(os.path.join(pdf_dir, f)) for f in pdf_files)

@pytest.mark.skipif(not exists, reason="PDF test files not present")
@pytest.mark.asyncio
async def test_real_pdfs_extraction():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        for pdf_name in pdf_files:
            path = os.path.join(pdf_dir, pdf_name)
            with open(path, "rb") as f:
                pdf_bytes = f.read()
            response = await client.post(
                "/extract",
                files={"file": (pdf_name, pdf_bytes, "application/pdf")},
            )
            assert response.status_code == 200
            json = response.json()
            assert isinstance(json.get("page_count"), int)
            content = json.get("content")
            assert isinstance(content, str) and content.strip() != ""
            # Ensure no leading > character for markdown blockquote style
            assert not content.lstrip().startswith(">")
