"""FastAPI application entry point for the PDF text extraction microservice."""

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from starlette.responses import JSONResponse

from app.api.v1.endpoints import router as v1_router
from app.core.errors import rfc9457_error

app = FastAPI(
    title="PDF Text Extraction Service",
    description="Microservice that extracts text from PDF documents using base64 encoding and pypdf",
    version="1.0.0",
)


@app.exception_handler(HTTPException)
async def rfc9457_http_exception_handler(request: Request, exc: HTTPException):
    """Convert HTTPException to RFC 9457 Problem Details format.

    Ensures error fields (type, title, status, detail) appear at the top level
    of the response body, not nested under a "detail" key.
    """
    error_detail = rfc9457_error(
        status_code=exc.status_code,
        title=exc.detail
        if isinstance(exc.detail, str)
        else exc.detail.get("title", "Error"),
        detail=exc.detail
        if isinstance(exc.detail, str)
        else exc.detail.get("detail", str(exc.detail)),
        instance=str(request.url.path),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_detail,
    )


app.include_router(v1_router, tags=["pdf-extraction"])


@app.get("/health", include_in_schema=False)
async def health_check():
    """Health check endpoint that verifies the service is operational.

    Returns real health status - not a mock that always returns True.
    """
    return {"status": "ok"}
