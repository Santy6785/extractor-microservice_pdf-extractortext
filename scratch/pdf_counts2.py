import os, sys, asyncio
from httpx import AsyncClient, ASGITransport
from pypdf import PdfReader

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from app.main import app

pdf_dir = os.path.abspath(os.path.join(project_root, 'tests', 'stress', 'pdfs'))
pdf_files = [
    "2020-Scrum-Guide-Spanish-Latin-South-American.pdf",
    "scrum_manager_historias_usuario.pdf",
    "Essential-Kanban-Condensed-Spanish.pdf",
    "Filosofia_Lean.pdf",
]

async def main():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        for pdf_name in pdf_files:
            path = os.path.join(pdf_dir, pdf_name)
            with open(path, "rb") as f:
                pdf_bytes = f.read()
            resp = await client.post("/extract", files={"file": (pdf_name, pdf_bytes, "application/pdf")})
            data = resp.json()
            service_page_count = data.get("page_count")
            reader = PdfReader(path)
            actual_page_count = len(reader.pages)
            print(f"{pdf_name}: service_page_count={service_page_count}, actual_page_count={actual_page_count}")

if __name__ == "__main__":
    asyncio.run(main())
