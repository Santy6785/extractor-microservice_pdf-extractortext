"""Data Transfer Objects for PDF text extraction."""

from pydantic import BaseModel


class ExtractRequest(BaseModel):
    """Request DTO for PDF text extraction.

    Contains the binary PDF file payload to be processed via multipart/form-data.
    """

    file: bytes

    model_config = {"json_schema_extra": {"example": {"file": b""}}}


class ExtractResponse(BaseModel):
    """Response DTO for PDF text extraction.

    Contains the extracted text in Markdown format and the page count.
    """

    content: str
    page_count: int

    model_config = {
        "json_schema_extra": {"example": {"content": "# Hello World", "page_count": 1}}
    }
