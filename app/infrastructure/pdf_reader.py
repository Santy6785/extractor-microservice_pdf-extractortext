"""pypdf infrastructure adapter - isolated behind interface.

Wraps pypdf.PdfReader to extract text from PDF bytes.
Does NOT import any FastAPI or HTTP types — pure infrastructure logic.
"""

from __future__ import annotations

import io
import re
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
        raise InfraExtractionError(f"Unexpected error extracting PDF text: {exc}") from exc


def _to_markdown(text: str, page_count: int) -> str:
    """Convert extracted plain text to a simple Markdown representation.

    The heuristic detects simple titles, bullet/numbered lists, and very basic tables.
    It does **not** aim to be perfect; complex structures are left as plain text.
    """
    if not text:
        return f"# PDF Extraction\n**Pages:** {page_count}\n\n*No text extracted*"

    lines = text.split("\n")
    result_lines: list[str] = []
    i = 0

    def is_title(line: str) -> bool:
        stripped = line.strip()
        return len(stripped) > 3 and stripped.isupper()

    def is_table_separator(line: str) -> bool:
        return bool(re.fullmatch(r"[\s-]+", line))

    while i < len(lines):
        line = lines[i].rstrip()
        if not line:
            result_lines.append("")
            i += 1
            continue
        if is_title(line):
            result_lines.append(f"# {line.strip()}")
            i += 1
            continue
        if re.match(r"^(\s*[-*+]\s+|\s*\d+\.\s+)", line):
            result_lines.append(line.strip())
            i += 1
            continue
        # Table detection
        if i + 1 < len(lines) and re.search(r"\s{2,}", line) and is_table_separator(lines[i + 1]):
            header_cells = [c.strip() for c in re.split(r"\s{2,}", line) if c.strip()]
            separator = "|".join(["---"] * len(header_cells))
            result_lines.append("| " + " | ".join(header_cells) + " |")
            result_lines.append("| " + separator + " |")
            i += 2
            while i < len(lines) and re.search(r"\s{2,}", lines[i]):
                row_cells = [c.strip() for c in re.split(r"\s{2,}", lines[i]) if c.strip()]
                if len(row_cells) == len(header_cells):
                    result_lines.append("| " + " | ".join(row_cells) + " |")
                else:
                    break
                i += 1
            continue
        # Default paragraph line
        result_lines.append(line)
        i += 1

    header = f"# PDF Extraction\n**Pages:** {page_count}\n"
    markdown = header + "\n".join(result_lines).rstrip("\n")
    return markdown
