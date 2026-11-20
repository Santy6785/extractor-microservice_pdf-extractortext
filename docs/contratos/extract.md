# Contrato: `POST /extract`

Extractor de PDF a Markdown. Ruta canónica `/extract`; alias `/api/v1/extract` (oculto del OpenAPI, ver `docs/decisiones.md` ADR-001).

## Request

Dos formas, ambas válidas:

| Content-Type | Cuerpo |
|---|---|
| `multipart/form-data` | campo `file` con el PDF |
| `application/pdf` o `application/octet-stream` | bytes crudos del PDF |

Cualquier otro `Content-Type` devuelve 415. Implementado en `app/api/v1/endpoints.py` (`_read_pdf`).

## Response 200

```json
{"content": "# Título\n\ntexto en Markdown...", "page_count": 16}
```

`Content-Type: application/json`. Modelo: `app/dtos/extraction.py` (`ExtractResponse`).

## Errores

Todos siguen el mismo formato (ver abajo) y llevan el header `X-Request-ID`.

| Status | `detail` | Cuándo | Código |
|---|---|---|---|
| 400 | `Missing multipart field 'file'` | multipart sin campo `file` | `endpoints.py` (`_read_pdf`) |
| 400 | `Not a PDF (missing %PDF- header)` | el cuerpo no empieza con `%PDF-` | `endpoints.py` (`extract_endpoint`) |
| 400 | `Extraction Failed` | error inesperado, no clasificado | `endpoints.py` (`except Exception`) |
| 413 | `PDF exceeds <N> MB` | `Content-Length` o body real mayor que `PDF_MAX_FILE_SIZE_MB` (default 50) | `endpoints.py` (inicio y tras leer) |
| 415 | `Use multipart/form-data, application/pdf or application/octet-stream` | `Content-Type` no soportado | `endpoints.py` (`_read_pdf`) |
| 422 | `PDF is corrupt or unreadable` | pymupdf no puede abrir o parsear el archivo | `endpoints.py` (`except InfraExtractionError`) |
| 422 | `PDF is password-protected` | el PDF requiere contraseña | `endpoints.py` (`except InfraExtractionError`) |
| 429 | `Queue is full` | cola de espera llena (`EXTRACT_MAX_QUEUE`) | `endpoints.py` (`_acquire_slot`) |
| 429 | `Queue timeout` | espera superó `EXTRACT_QUEUE_TIMEOUT` | `endpoints.py` (`_acquire_slot`) |

Los 429 incluyen `Retry-After: 1`.

## Formato de error

```json
{
  "type": "/extract",
  "title": "Unprocessable Entity",
  "status": 422,
  "detail": "PDF is password-protected",
  "instance": "/extract"
}
```

Generado en `app/main.py` (handler de `HTTPException`) y `app/core/errors.py`.

**Desvío de RFC 9457 que hay que conocer:** `type` repite el path de la petición en lugar de ser una URI que documente el tipo de problema. `Content-Type` es `application/json`, no `application/problem+json`. Ambos desvíos son deliberados por ahora; si se corrigen, cambia este contrato.

## Headers

- `X-Request-ID`: si el cliente envía uno válido (1 a 128 caracteres, `[A-Za-z0-9._-]`), se devuelve el mismo; si no, se genera uno. Presente en todas las respuestas (`app/core/observability.py`).

## Límites

- Tamaño: `PDF_MAX_FILE_SIZE_MB` (default 50). Un upload chunked sin `Content-Length` se lee completo antes de validar el tamaño.
- Concurrencia: `EXTRACT_CONCURRENCY` extracciones en paralelo por réplica; `EXTRACT_MAX_QUEUE` esperando; `EXTRACT_QUEUE_TIMEOUT` segundos de espera máxima.
- Caché: `EXTRACT_CACHE_SIZE` entradas por réplica, por sha256 del PDF (0 la desactiva).

## Health

`GET /health` devuelve `{"status": "ok"}` de forma estática. **No verifica nada real**; no sirve como señal de salud hasta que se implemente.
