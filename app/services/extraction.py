"""PDF text extraction business logic service.

Orchestrates: base64 decode → pypdf infrastructure adapter → DTO response.

Follows strict N-layers architecture: Presentation -> Services -> Infrastructure.
The service layer does NOT import from infrastructure directly beyond the
abstract interface contract — it uses the infrastructure adapter as a dependency.
"""

import base64

from app.dtos.extraction import ExtractResponse
from app.infrastructure.pdf_reader import InfraExtractionError, extract_text


def extract_pdf_text(base64_pdf: str) -> ExtractResponse:
    """Extract text from a base64-encoded PDF document.

    Args:
        base64_pdf: Base64-encoded PDF file content.

    Returns:
        ExtractResponse DTO with the extracted text and processing status.

    Raises:
        InfraExtractionError: If the PDF cannot be decoded or text extraction fails.
    """
    try:
        pdf_bytes = base64.b64decode(base64_pdf, validate=True)
    except Exception as exc:
        raise InfraExtractionError(f"Invalid base64 encoding: {exc}") from exc

    try:
        extracted_text = extract_text(pdf_bytes)
    except InfraExtractionError:
        raise
    except Exception as exc:
        raise InfraExtractionError(f"PDF text extraction failed: {exc}") from exc

    if extracted_text is None:
        extracted_text = ""

    return ExtractResponse(extracted_text=extracted_text, status="processed")
