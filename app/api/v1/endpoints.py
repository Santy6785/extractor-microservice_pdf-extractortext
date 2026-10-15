"""API endpoints for PDF text extraction microservice.

Follows strict N-layers architecture:
- Presentation layer (this file) → Services layer → Infrastructure layer
- API layer never imports from infrastructure directly
- All errors follow RFC 9457 (Problem Details for HTTP APIs)
- Backpressure with asyncio.Semaphore to prevent overload/timeout.
"""

import asyncio

from fastapi import APIRouter, Form, UploadFile
from fastapi.exceptions import HTTPException

from app.core.errors import rfc9457_error
from app.dtos.extraction import ExtractResponse
from app.services.extraction import extract_pdf_text
from app.infrastructure.pdf_reader import InfraExtractionError

router = APIRouter(prefix="/api/v1", tags=["pdf-extraction"])

# Backpressure: semáforo con límite de 5 concurrencia para devolver 429/503
_CONCURRENCY_LIMIT = 5
_semaphore = asyncio.Semaphore(_CONCURRENCY_LIMIT)


@router.post("/extract", response_model=ExtractResponse)
async def extract_endpoint(file: UploadFile = Form(...)) -> ExtractResponse:
    """Extract text from a PDF document received as binary via multipart/form-data.

    FastAPI requiere Form(...) en el parámetro para parsear datos multipart.
    Accepta un PDF subido como multipart/form-data con el campo "file".
    Devuelve el texto extraído en formato Markdown y el conteo de páginas.

    Devuelve 429 Too Many Requests si se alcanza el límite de concurrencia (backpressure).
    Devuelve 400 Problem Details (RFC 9457) para entradas inválidas o fallos de extracción.
    """
    # Intentar adquirir un slot con timeout corto (aprox. 10ms)
    # Si no se libera en ese tiempo, la cola está saturada
    try:
        await asyncio.wait_for(_semaphore.acquire(), timeout=0.01)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=429, detail="Too Many Requests")

    # Ensure release after processing (even if error)
    acquired = True

    try:
        try:
            pdf_bytes = asyncio.wait_for(file.read(), timeout=30.0)
        except asyncio.TimeoutError:
            error_detail = rfc9457_error(400, "Extraction Failed", "PDF read timed out")
            raise HTTPException(status_code=400, detail=error_detail)

        result = extract_pdf_text(pdf_bytes)
        return result
    except HTTPException:
        # Re-lanzar HTTPException manteniendo código y detalle
        raise
    except Exception as exc:
        error_detail = rfc9457_error(400, "Extraction Failed", str(exc))
        raise HTTPException(status_code=400, detail=error_detail)
    finally:
        if acquired:
            _semaphore.release()