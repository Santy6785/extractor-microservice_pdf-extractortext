"""PDF text extraction business logic service.

Orchestrates: binary PDF bytes → pypdf infrastructure adapter → Markdown response DTO.

Follows strict N-layers architecture: Presentation -> Services -> Infrastructure.
The service layer does NOT import from infrastructure directly beyond the
abstract interface contract — it uses the infrastructure adapter as a dependency.
"""



from app.dtos.extraction import ExtractResponse
from app.infrastructure.pdf_reader import InfraExtractionError, extract_text


def extract_pdf_text(pdf_bytes: bytes) -> ExtractResponse:
    """Extract text from a binary PDF document and convert to Markdown.

    Args:
        pdf_bytes: Raw PDF file bytes.

    Returns:
        ExtractResponse DTO with the extracted text in Markdown format
        and the page count.

    Raises:
        InfraExtractionError: If the PDF cannot be decoded or text extraction fails.
    """
    try:
        extracted_text, page_count = extract_text(pdf_bytes)
    except InfraExtractionError:
        raise
    except Exception as exc:
        raise InfraExtractionError(f"PDF text extraction failed: {exc}") from exc

    if extracted_text is None:
        extracted_text = ""

    return ExtractResponse(content=extracted_text, page_count=page_count)