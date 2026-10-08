"""pypdf infrastructure adapter - isolated behind interface.

Wraps pypdf.PdfReader to extract text from PDF bytes.
Does NOT import any FastAPI or HTTP types — pure infrastructure logic.
"""

from __future__ import annotations

import io

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class InfraExtractionError(Exception):
    """Raised when PDF text extraction fails at the infrastructure layer."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def extract_text(pdf_bytes: bytes) -> str | None:
    """Extract text from PDF bytes using pypdf.

    Args:
        pdf_bytes: Raw PDF file bytes.

    Returns:
        Extracted text content, or None if no text found.

    Raises:
        InfraExtractionError: If the PDF cannot be read or parsed.
    """
    if not pdf_bytes:
        raise InfraExtractionError("PDF bytes are empty")

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        text_parts: list[str] = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text.strip())
        return "\n".join(text_parts) if text_parts else None
    except PdfReadError as exc:
        raise InfraExtractionError(f"Failed to read PDF: {exc}") from exc
    except Exception as exc:
        raise InfraExtractionError(
            f"Unexpected error extracting PDF text: {exc}"
        ) from exc
