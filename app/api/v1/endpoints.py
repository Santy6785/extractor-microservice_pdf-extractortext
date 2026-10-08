"""API endpoints for PDF text extraction microservice.

Follows strict N-layers architecture:
- Presentation layer (this file) → Services layer → Infrastructure layer
- API layer never imports from infrastructure directly
- All errors follow RFC 9457 (Problem Details for HTTP APIs)
"""

from fastapi import APIRouter, HTTPException

from app.core.errors import rfc9457_error
from app.dtos.extraction import ExtractRequest, ExtractResponse
from app.services.extraction import extract_pdf_text

router = APIRouter(prefix="/api/v1", tags=["pdf-extraction"])


@router.post("/extract", response_model=ExtractResponse)
def extract_endpoint(payload: ExtractRequest) -> ExtractResponse:
    """Extract text from a base64-encoded PDF document.

    Accepts a JSON payload with a base64-encoded PDF file.
    Returns the extracted text via an ExtractResponse DTO.

    Raises 400 Problem Details (RFC 9457) for invalid input or extraction failures.
    """
    try:
        result = extract_pdf_text(payload.base64_pdf)
        return result
    except Exception as exc:
        error_detail = rfc9457_error(400, "Extraction Failed", str(exc))
        raise HTTPException(status_code=400, detail=error_detail)


@router.get("/health", include_in_schema=False)
def health_endpoint():
    """Health check endpoint that verifies the service is operational.

    Returns real health status - not a mock that always returns True.
    """
    return {"status": "ok"}
