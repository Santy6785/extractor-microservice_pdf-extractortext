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


def extract_text(pdf_bytes: bytes) -> tuple[str, int]:
    """Extract text from PDF bytes using pypdf and convert to Markdown.

    Args:
        pdf_bytes: Raw PDF file bytes.

    Returns:
        A tuple of (markdown_text, page_count).
        markdown_text is the extracted content converted to Markdown format.
        page_count is the number of pages in the PDF.

    Raises:
        InfraExtractionError: If the PDF cannot be read or parsed.
    """
    if not pdf_bytes:
        raise InfraExtractionError("PDF bytes are empty")

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        page_count = len(reader.pages)
        text_parts: list[str] = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text.strip())
        raw_text = "\n".join(text_parts) if text_parts else ""

        markdown = _to_markdown(raw_text, page_count)

        return markdown, page_count
    except PdfReadError as exc:
        raise InfraExtractionError(f"Failed to read PDF: {exc}") from exc
    except Exception as exc:
        raise InfraExtractionError(
            f"Unexpected error extracting PDF text: {exc}"
        ) from exc


def _to_markdown(text: str, page_count: int) -> str:
    """Convert plain text to Markdown format.

    Adds a header with page count and ensures proper formatting.
    """
    if not text:
        return f"# PDF Extraction\n**Pages:** {page_count}\n\n*No text extracted*"

    # Create a level-1 header with page count, then the content
    markdown = f"# PDF Extraction\n**Pages:** {page_count}\n\n"
    # Preserve paragraphs by splitting on double newlines
    paragraphs = text.split("\n\n")
    for i, para in enumerate(paragraphs):
        para_stripped = para.strip()
        if para_stripped:
            # Add blockquote for multi-line paragraphs if needed
            lines = [l for l in para_stripped.split("\n") if l.strip()]
            if len(lines) > 1:
                markdown += f"> {lines[0]}\n"
                for line in lines[1:]:
                    markdown += f"> {line}\n"
            else:
                markdown += f"{lines[0]}\n"

    return markdown.rstrip("\n")