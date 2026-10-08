# Plan: PDF Text Extraction Microservice

## Components and Dependencies

| Component | Responsibility | Depends On |
|---|---|---|
| `core/config` | Application configuration | — |
| `core/errors` | RFC 9457 error helpers | — |
| `dtos/extraction` | Request/response DTOs | — |
| `infrastructure/pdf_reader` | pypdf adapter (wraps pypdf library) | — |
| `services/extraction` | Business logic: orchestrate PDF extraction | `infrastructure/pdf_reader` |
| `api/v1/endpoints` | HTTP presentation layer | `services/extraction`, `core/errors` |
| `main` | FastAPI app wiring | `api/v1/endpoints` |

**Build order:** `core/config, core/errors, dtos/extraction` → `infrastructure/pdf_reader` → `services/extraction` → `api/v1/endpoints` → `main`

## Risks and Mitigation

| Risk | Mitigation |
|---|---|
| pypdf fails on encrypted/corrupt PDFs | Validate PDF magic bytes before extraction; catch pypdf-specific exceptions and map to RFC 9457 |
| RFC 9457 formatting drift | Centralize error formatting in `core/errors`; use single source of truth |
| Architecture violation (API layer importing infra) | Enforce strict dependency direction via code review; `api` never imports `infrastructure` directly |

## Verification Checkpoints

- [ ] `core/config` loads without errors
- [ ] `dtos/extraction` validates request/response shapes
- [ ] `infrastructure/pdf_reader` extracts text from valid PDF bytes
- [ ] `services/extraction` uses only `infrastructure/pdf_reader` interface
- [ ] `api/v1/endpoints` returns RFC 9457 errors for invalid input
- [ ] `main` wires all components together
- [ ] Test suite passes with ≥80% coverage on `services/` and `infrastructure/`

## Parallel vs Sequential

- **Sequential:** `core/` → `infrastructure/pdf_reader` → `services/extraction` → `api/v1/endpoints` (each layer depends on the one below)
- **Parallel possible after layer completion:** Unit tests for each module can run in parallel once their respective source is stable