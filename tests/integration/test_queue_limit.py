"""Integration tests for bounded waiting queue on the /extract endpoint - Task 6a."""

import asyncio
import os
import pytest
from httpx import AsyncClient, ASGITransport

from app.api.v1 import endpoints
from app.main import app

pdf_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "stress", "pdfs"))
real_pdf_path = os.path.join(pdf_dir, "2020-Scrum-Guide-Spanish-Latin-South-American.pdf")


@pytest.mark.asyncio
async def test_bounded_queue_second_waits_third_gets_429():
    """Verify that with extract_max_queue=1 and busy semaphore:
    - 2nd request waits in queue.
    - 3rd request immediately receives 429.
    - When semaphore is released, 2nd request completes successfully with 200.
    """
    if os.path.isfile(real_pdf_path):
        with open(real_pdf_path, "rb") as f:
            pdf_bytes = f.read()
    else:
        pdf_bytes = (
            b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj "
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj "
            b"3 0 obj<</Type/Page/MediaBox[0 0 72 72]/Parent 2 0 R>>endobj\n"
            b"xref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n"
            b"0000000060 00000 n\n0000000120 00000 n\ntrailer<</Size 4/Root 1 0 R>>\n"
            b"startxref\n190\n%%EOF"
        )

    orig_max_queue = endpoints.settings.extract_max_queue
    orig_sem = endpoints._semaphore
    orig_esperando = endpoints._esperando

    try:
        endpoints.settings.extract_max_queue = 1
        endpoints.settings.extract_queue_timeout = 5.0
        endpoints._semaphore = asyncio.Semaphore(1)
        endpoints._esperando = 0

        # 1. Occupy the semaphore to simulate in-flight request
        await endpoints._semaphore.acquire()
        assert endpoints._semaphore.locked() is True
        assert endpoints._esperando == 0

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # 2. Launch 2nd request: semaphore is busy, so it must enter the queue and wait
            task2 = asyncio.create_task(
                client.post(
                    "/extract",
                    files={"file": ("doc2.pdf", pdf_bytes, "application/pdf")},
                )
            )

            # Allow task2 to run and enter the queue
            await asyncio.sleep(0.05)
            assert endpoints._esperando == 1, "Second request should be waiting in queue"
            assert not task2.done(), "Second request should still be waiting"

            # 3. 3rd request arrives while waiting queue is full (esperando >= max_queue)
            # Should immediately receive 429 without waiting
            start_time = asyncio.get_event_loop().time()
            resp3 = await client.post(
                "/extract",
                files={"file": ("doc3.pdf", pdf_bytes, "application/pdf")},
            )
            elapsed = asyncio.get_event_loop().time() - start_time

            assert resp3.status_code == 429, f"Expected 429, got {resp3.status_code}: {resp3.text}"
            assert elapsed < 1.0, f"429 response should be immediate, took {elapsed:.2f}s"
            assert resp3.headers.get("retry-after") == "1"
            body3 = resp3.json()
            assert "detail" in body3
            assert body3.get("status") == 429

            # 4. Release the semaphore so 2nd request can acquire it and finish
            endpoints._semaphore.release()

            resp2 = await task2
            assert resp2.status_code == 200, f"Expected 200 for waiting request, got {resp2.status_code}"
            assert endpoints._esperando == 0, "Waiting queue counter should be decremented to 0"
            body2 = resp2.json()
            assert "content" in body2
            assert "page_count" in body2
    finally:
        # Restore original state
        endpoints.settings.extract_max_queue = orig_max_queue
        endpoints._semaphore = orig_sem
        endpoints._esperando = orig_esperando
