# Task List: PDF Text Extraction Microservice

## Task 1: Setup Core Configuration and Error Types
- **Acceptance:** `core/config.py` exports settings; `core/errors.py` provides `rfc9457_error(status_code, title, detail, instance)` function that returns RFC 9457 compliant dict
- **Verify:** `python -c "from app.core.config import Settings; s = Settings(); print(s)"` succeeds; `python -c "from app.core.errors import rfc9457_error; print(rfc9457_error(400, 'Bad Request', 'Invalid input', '/api/extract'))"` returns valid Problem Details JSON
- **Files:** `app/core/config.py`, `app/core/errors.py`
- **TDD:** Write test first that fails (test imports fail), then implement, then refactor

## Task 2: Define DTOs for Request/Response
- **Acceptance:** `dtos/extraction.py` defines `ExtractRequest(base64_pdf: str)` and `ExtractResponse(extracted_text: str, status: str)` using Pydantic BaseModel; both have type hints and docstrings
- **Verify:** `python -c "from app.dtos.extraction import ExtractRequest, ExtractResponse; r = ExtractRequest(base64_pdf='dummy'); print(r)"` works; can serialize/deserialize JSON
- **Files:** `app/dtos/extraction.py`
- **TDD:** Write test defining expected DTO behavior, implement DTO, verify

## Task 3: Implement pypdf Infrastructure Adapter
- **Acceptance:** `infrastructure/pdf_reader.py` implements `extract_text(pdf_bytes: bytes) -> Optional[str]` using pypdf.PdfReader; raises `InfraExtractionError` (custom exception) on failure
- **Verify:** Test with a small valid PDF bytes; test that invalid bytes raise error; adapter does not import FastAPI or HTTP types
- **Files:** `app/infrastructure/pdf_reader.py`
- **TDD:** Write test that calls `extract_text` with mock PDF bytes, expect text output or error; implement adapter

## Task 4: Implement Extraction Service (Business Logic)
- **Acceptance:** `services/extraction.py` provides `extract_pdf_text(base64_pdf: str) -> ExtractResponse`; it decodes base64 → calls infra adapter → returns DTO; no FastAPI imports in this file
- **Verify:** Test with valid base64 PDF → gets text; test with invalid base64 → gets RFC 9457 error via exception handling; test with corrupt PDF → gets error
- **Files:** `app/services/extraction.py`
- **TDD:** Write test for the service function, implement, verify

## Task 5: Implement API Endpoints
- **Acceptance:** `api/v1/endpoints.py` defines `POST /api/v1/extract` handler that receives `ExtractRequest`, calls service, returns `ExtractResponse`; `POST /api/v1/health` returns health status; all errors use `core.errors.rfc9457_error` mapped to proper HTTP exceptions
- **Verify:** `httpx.AsyncClient` test: POST valid payload → 200 with extracted text; POST invalid base64 → 400 with Problem Details; POST corrupt base64 → 422/400 with Problem Details
- **Files:** `app/api/v1/endpoints.py`
- **TDD:** Write integration test hitting the endpoint, implement endpoint, verify

## Task 6: Wire App Entry Point
- **Acceptance:** `app/main.py` creates FastAPI app, includes router from `api.v1.endpoints`, configures CORS if needed; health endpoint at `/health` does real health check (not try/except that always returns True)
- **Verify:** `python -m uvicorn app.main:app --reload` starts server; GET /health returns 200; POST /api/v1/extract works via HTTP
- **Files:** `app/main.py`
- **TDD:** Write test that client hits /health and /extract, implement main, verify

## Task 7: Write Comprehensive Test Suite
- **Acceptance:** All modules have unit tests in `tests/unit/`; integration tests in `tests/integration/`; no tautological tests (each test validates actual behavior)
- **Verify:** `python -m pytest --cov=app tests/` passes with ≥80% coverage on core/modules
- **Files:** `tests/unit/`, `tests/integration/`
- **TDD:** This task runs throughout — tests written for each preceding task

## Task 8: Code Review and Refinement
- **Acceptance:** No "God Classes"; dependency direction is strict (downward only); naming uses lowercase; KISS/DRY principles applied; Health Check is real, not mock
- **Verify:** `python -m ruff check .` passes; `python -m ruff format .` passes; manual review of dependency imports
- **Files:** All source files
- **TDD:** Refactor based on lint/test feedback