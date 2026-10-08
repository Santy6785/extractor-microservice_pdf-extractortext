"""Data Transfer Objects for PDF text extraction."""

from pydantic import BaseModel


class ExtractRequest(BaseModel):
    """Request DTO for PDF text extraction.

    Contains the base64-encoded PDF payload to be processed.
    """

    base64_pdf: str

    model_config = {"json_schema_extra": {"example": {"base64_pdf": "JVBERi0xLjQK"}}}


class ExtractResponse(BaseModel):
    """Response DTO for PDF text extraction.

    Contains the extracted text and processing status.
    """

    extracted_text: str
    status: str = "processed"

    model_config = {
        "json_schema_extra": {
            "example": {"extracted_text": "Hello World", "status": "processed"}
        }
    }
