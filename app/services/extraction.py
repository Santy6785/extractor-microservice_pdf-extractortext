"""PDF text extraction business logic service.

Orchestrates: binary PDF bytes -> pymupdf infrastructure adapter -> Markdown response DTO.

Follows strict N-layers architecture: Presentation -> Services -> Infrastructure.
The service layer does NOT import from infrastructure directly beyond the
abstract interface contract - it uses the infrastructure adapter as a dependency.
"""

from __future__ import annotations

import hashlib

from app.dtos.extraction import ExtractResponse
from app.infrastructure.pdf_reader import InfraExtractionError, extract_text
from app.services import cache
from app.services.markdown import to_markdown


def extract_pdf_text(pdf_bytes: bytes) -> ExtractResponse:
    """Extract text from a binary PDF document and convert to Markdown.

    Checks the LRU cache before extracting. On cache miss, extracts text,
    converts to Markdown, caches the response, and returns it.

    Args:
        pdf_bytes: Raw PDF file bytes.

    Returns:
        ExtractResponse DTO with the extracted text in Markdown format
        and the page count.

    Raises:
        InfraExtractionError: If the PDF cannot be decoded or text extraction fails.
    """
    raw_bytes = pdf_bytes if isinstance(pdf_bytes, (bytes, bytearray)) else str(pdf_bytes).encode("utf-8")
    cache_key = hashlib.sha256(raw_bytes).hexdigest()

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        extracted_text, page_count = extract_text(pdf_bytes)
    except InfraExtractionError:
        raise
    except Exception as exc:
        raise InfraExtractionError(f"PDF text extraction failed: {exc}") from exc

    content = to_markdown(extracted_text or "")
    response = ExtractResponse(content=content, page_count=page_count)
    cache.put(cache_key, response)
    return response
