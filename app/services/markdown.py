"""Lightweight plain-text to Markdown converter for extracted PDF text.

Performs:
- Normalization of bullets (-, *, +, •, etc.) to "- ".
- Detection and marking of short uppercase or numbered lines as headings (# ...).
- Separation of paragraphs with double newlines.
"""

from __future__ import annotations

import re


def is_short_line(line: str, max_words: int = 10, max_chars: int = 80) -> bool:
    """Check if a line is short enough to be considered a heading."""
    stripped = line.strip()
    return 0 < len(stripped) <= max_chars and len(stripped.split()) <= max_words


def is_uppercase_heading(line: str) -> bool:
    """Return True if line is short and all letters are uppercase."""
    stripped = line.strip()
    if not is_short_line(stripped):
        return False
    letters = [c for c in stripped if c.isalpha()]
    return bool(letters) and stripped.isupper()


def is_numbered_heading(line: str) -> bool:
    """Return True if line is short and begins with numbering like '1. ', '1.1 '."""
    stripped = line.strip()
    if not is_short_line(stripped):
        return False
    return bool(re.match(r"^\d+(\.\d+)*[.)]?\s+\S+", stripped))


def is_heading(line: str) -> bool:
    """Check if a line qualifies as a heading."""
    stripped = line.strip()
    if stripped.startswith("#"):
        return True
    return is_uppercase_heading(stripped) or is_numbered_heading(stripped)


def format_heading(line: str) -> str:
    """Format a line as a Markdown heading."""
    stripped = line.strip()
    if stripped.startswith("#"):
        return stripped
    return f"# {stripped}"


def is_bullet(line: str) -> bool:
    """Check if a line starts with a bullet marker."""
    stripped = line.strip()
    return bool(re.match(r"^[-*+•–—]\s+", stripped))


def format_bullet(line: str) -> str:
    """Convert a bullet marker to '- '."""
    stripped = line.strip()
    return re.sub(r"^[-*+•–—]\s+", "- ", stripped)


def to_markdown(text: str) -> str:
    """Convert plain text to lightweight Markdown."""
    if not text or not text.strip():
        return ""

    lines = text.splitlines()
    blocks: list[str] = []
    current_lines: list[str] = []
    current_type: str | None = None

    def flush():
        nonlocal current_lines, current_type
        if current_lines:
            blocks.append("\n".join(current_lines))
            current_lines = []
            current_type = None

    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            flush()
            continue

        if is_heading(stripped):
            flush()
            blocks.append(format_heading(stripped))
        elif is_bullet(stripped):
            if current_type != "bullet":
                flush()
                current_type = "bullet"
            current_lines.append(format_bullet(stripped))
        else:
            if current_type != "text":
                flush()
                current_type = "text"
            current_lines.append(stripped)

    flush()
    return "\n\n".join(blocks)


def convert_to_markdown(text: str) -> str:
    """Alias for to_markdown."""
    return to_markdown(text)


__all__ = [
    "is_short_line",
    "is_uppercase_heading",
    "is_numbered_heading",
    "is_heading",
    "format_heading",
    "is_bullet",
    "format_bullet",
    "to_markdown",
    "convert_to_markdown",
]
