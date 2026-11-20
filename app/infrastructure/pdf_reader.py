"""PDF extraction infrastructure using pymupdf.

Provides a thin wrapper that extracts raw text from PDF bytes and returns the text together with the page count.
The public API:
    extract_text(pdf_bytes: bytes) -> tuple[str, int]
"""

from __future__ import annotations

import pymupdf


class InfraExtractionError(Exception):
    """Raised when PDF text extraction fails at the infrastructure layer.

    ``kind`` tells the API layer why: "corrupt" (default) or "encrypted".
    """

    def __init__(self, message: str, kind: str = "corrupt") -> None:
        super().__init__(message)
        self.message = message
        self.kind = kind


def extract_text(pdf_bytes: bytes) -> tuple[str, int]:
    """Extract raw text from PDF bytes using pymupdf.

    Args:
        pdf_bytes: Raw PDF file bytes.

    Returns:
        A tuple (raw_text, page_count) where raw_text is the concatenated plain text of all pages.

    Raises:
        InfraExtractionError: kind="corrupt" if the PDF cannot be parsed,
            kind="encrypted" if it requires a password.
    """
    if not pdf_bytes:
        raise InfraExtractionError("PDF bytes are empty")
    try:
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise InfraExtractionError(f"Failed to extract PDF text: {exc}") from exc
    try:
        if doc.needs_pass:
            raise InfraExtractionError("PDF is password-protected", kind="encrypted")
        page_count = len(doc)
        text_parts: list[str] = []
        for page in doc:
            txt = page.get_text()
            if txt:
                text_parts.append(txt.strip())
        raw_text = "\n".join(text_parts) if text_parts else ""
        return raw_text, page_count
    except InfraExtractionError:
        raise
    except Exception as exc:
        raise InfraExtractionError(f"Failed to extract PDF text: {exc}") from exc
    finally:
        doc.close()
