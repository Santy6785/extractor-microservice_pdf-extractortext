# Spec: PDF Text Extraction Microservice

## Objective
Build a FastAPI microservice that extracts text from PDF documents provided as base64-encoded payloads. The service accepts a JSON payload containing a base64-encoded PDF, decodes it, extracts text using pypdf, and returns the extracted text via a DTO in JSON format. A health check endpoint verifies service availability.

**User:** Backend systems and frontend clients needing PDF text extraction capabilities.
**Success:** Extracted text is accurately returned in a structured JSON DTO; invalid PDFs return RFC 9457 error details; service health is verifiable via /health endpoint.

## Tech Stack
- Python 3.11+
- FastAPI 0.104+
- pypdf 3.0+
- Uvicorn 0.27+ (ASGI server)
- Pydantic 2.5+ (for DTOs)

## Commands
- Build: `python -m pip install -r requirements.txt && python -m pytest`
- Test: `python -m pytest`
- Lint: `python -m ruff check . --fix`
- Dev: `python -m uvicorn app.main:app --reload`
- Format: `python -m ruff format .`

## Project Structure
```
app/                      → Application source code (lowercase)
  main.py                 → Entry point and FastAPI app setup
  api/                    → Presentation layer (endpoints)
    - v1/                 → API versioning
      - endpoints.py      → HTTP endpoint handlers
  services/               → Business logic layer
    - extraction.py       → PDF extraction service (pypdf wrapper)
    - errors.py           → Error handling helpers (RFC 9457)
  dtos/                   → Data transfer objects
    - extraction.py       → Request/response DTOs
  infrastructure/         → Infra-adapter layer
    - pdf_reader.py       → pypdf adapter (isolated behind interface)
  core/                   → Core concerns
    - config.py           → Configuration/settings
tests/                    → Unit and integration tests
  unit/                   → Unit tests
  integration/            → Integration tests
e2e/                      → End-to-end tests
docs/                     → Documentation
requirements.txt          → Python dependencies
pyproject.toml            → Project config + FastAPI setup
```

## Code Style
- Lowercase module/package names (portability)
- Type hints throughout
- 88-char line width
- Docstrings for all public modules

**Example snippet (services/extraction.py):**
```python
from pypdf import PdfReader
from typing import Optional


def extract_text(pdf_bytes: bytes) -> Optional[str]:
    """Extract text from PDF bytes using pypdf."""
    try:
        reader = PdfReader(bytes=pdf_bytes)
        text_parts = []
        for page in reader.pages:
            text_parts.append(page.extract_text())
        return "\n".join(text_parts) if text_parts else None
    except Exception as exc:
        raise ExtractionError(f"Failed to extract text: {exc}")
```

## Testing Strategy
- Framework: pytest + httpx for async HTTP tests
- Unit tests live in `tests/unit/`
- Integration tests live in `tests/integration/`
- Coverage minimum: 80% for business logic
- Test levels:
  - Unit: Extraction service, DTO validation, error formatting
  - Integration: Full HTTP request/response cycle
  - E2E: `e2e/` directory for complete workflows

**No tautological tests** — tests must validate actual behavior, not variable-equals-self assertions.

## Boundaries
- **Always:** Run tests before commits; follow naming conventions; validate inputs
- **Ask first:** Database schema changes; adding external dependencies; changing CI config
- **Never:** Commit secrets; edit vendor directories; remove failing tests without approval

## Success Criteria
- [ ] POST /api/v1/extract returns 200 with JSON DTO containing extracted text
- [ ] POST /api/v1/extract with invalid base64 returns 400 Problem Details (RFC 9457)
- [ ] POST /api/v1/extract with invalid/corrupt PDF returns 422/400 Problem Details
- [ ] GET /health returns 200 with {"status": "ok"} or equivalent health payload
- [ ] All services layer dependencies flow downward only (no upward imports)
- [ ] Test suite passes with ≥80% coverage on core modules
- [ ] No "God Classes" — extraction logic isolated behind interface

## Open Questions
- Should the API support pagination for very long PDFs (partial text extraction)?
- Should text extraction include formatting/structure preservation or raw text only?
- What maximum PDF size should be enforced (memory considerations)?

**Next: Create implementation plan and task breakdown.**