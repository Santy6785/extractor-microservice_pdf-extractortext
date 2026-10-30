"""API endpoints for PDF text extraction microservice.

This version follows the updated specification:
- No router prefix; the router is mounted at the root and also aliased under /api/v1.
- Concurrency control uses settings.extract_concurrency and settings.extract_queue_timeout.
- Bounded waiting queue uses settings.extract_max_queue.
- Handles three content types: multipart/form-data with a `file` field, `application/pdf`, and `application/octet-stream`.
- Returns RFC 9457 compliant errors.
"""

import asyncio
from fastapi import APIRouter, Request, HTTPException
from app.core.errors import rfc9457_error
from app.core.config import Settings
from app.dtos.extraction import ExtractResponse
from app.services.extraction import extract_pdf_text

settings = Settings()

router = APIRouter(tags=["pdf-extraction"])  # No prefix

_semaphore = asyncio.Semaphore(settings.extract_concurrency)
_esperando: int = 0

async def _read_pdf(request: Request) -> bytes:
    ct = request.headers.get("content-type", "").lower()
    if ct.startswith("multipart/form-data"):
        form = await request.form()
        upload = form.get("file")
        if upload is None or not hasattr(upload, "read"):
            raise HTTPException(
                status_code=400,
                detail=rfc9457_error(400, "Bad Request", "Missing multipart field 'file'")
            )
        return await upload.read()
    if ct.startswith(("application/pdf", "application/octet-stream")):
        return await request.body()
    raise HTTPException(
        status_code=415,
        detail=rfc9457_error(
            415,
            "Unsupported Media Type",
            "Use multipart/form-data, application/pdf or application/octet-stream",
        ),
    )

@router.post("/extract", response_model=ExtractResponse)
async def extract_endpoint(request: Request) -> ExtractResponse:
    global _esperando
    if not _semaphore.locked():
        await _semaphore.acquire()
    else:
        if settings.extract_max_queue > 0 and _esperando >= settings.extract_max_queue:
            raise HTTPException(
                status_code=429,
                detail=rfc9457_error(429, "Too Many Requests", "Queue is full"),
                headers={"Retry-After": "1"},
            )
        _esperando += 1
        try:
            await asyncio.wait_for(_semaphore.acquire(), timeout=settings.extract_queue_timeout)
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=429,
                detail=rfc9457_error(429, "Too Many Requests", "Queue timeout"),
                headers={"Retry-After": "1"},
            )
        finally:
            _esperando -= 1

    try:
        pdf_bytes = await _read_pdf(request)
        if not pdf_bytes.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=400,
                detail=rfc9457_error(400, "Bad Request", "Not a PDF (missing %PDF- header)"),
            )
        return await asyncio.to_thread(extract_pdf_text, pdf_bytes)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=rfc9457_error(400, "Extraction Failed", str(exc)))
    finally:
        _semaphore.release()
