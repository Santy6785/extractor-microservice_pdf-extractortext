# Decisiones de arquitectura (ADR)

## ADR-001: Rutas `/extract` y alias `/api/v1/extract`

**Estado:** aceptada.

**Contexto:** el router de extracción se monta dos veces en `app/main.py` (líneas 37-38): en la raíz y bajo `/api/v1` con `include_in_schema=False`. Traefik enruta solo `PathPrefix(/extract)` (`docker-compose.yml`, label `traefik.http.routers.extractor.rule`), así que `/api/v1/extract` no pasa por el gateway.

**Decisión:** `/extract` es la ruta canónica y la única documentada en el OpenAPI. `/api/v1/extract` queda como alias para clientes internos que llaman directo al servicio, sin cambiar el contrato.

**Consecuencias:** el alias no está publicado en Traefik. Quien lo use desde afuera de la red Docker tiene que ir directo al servicio. El contrato de errores es el mismo en ambas rutas (`docs/contratos/extract.md`).

## ADR-002: Biblioteca de extracción: pymupdf

**Estado:** aceptada.

**Contexto:** se compararon pypdf, pypdfium2 y pymupdf sobre los 4 PDFs del dataset. Los números salen de `docs/benchmarks/bench_libs.txt` (mediana de 3 corridas).

**Decisión:** pymupdf. Es 10 a 40 veces más rápida que pypdf y conserva el orden del texto. pypdfium2 es rápida, pero en `Filosofia_Lean.pdf` devolvió fragmentos desordenados.

**Consecuencias:**
- Licencia AGPL. Hay que mencionarla en el informe y valorarla si el proyecto se distribuye.
- Se fija `pymupdf>=1.24,<2` en `pyproject.toml`. La versión 2.x arrastra dependencias pesadas (onnxruntime, numpy, pymupdf-layout) que no se usan.

## ADR-003: Caché de resultados por sha256, por réplica

**Estado:** aceptada.

**Contexto:** el mismo PDF se pide muchas veces en la prueba de carga. Extraer cuesta CPU y la clave del caché es el contenido del archivo.

**Decisión:** LRU en memoria, clave sha256 del PDF, `EXTRACT_CACHE_SIZE` entradas (default 32, 0 lo desactiva). Cada réplica tiene su propio caché (`app/services/cache.py`).

**Consecuencias:**
- El caché no se comparte entre réplicas. Una réplica fría paga la extracción completa la primera vez.
- Sin TTL. La memoria crece hasta el tope de entradas.
- Pendiente de confirmar con el profesor si el caché es válido para el puntaje extra. Si no lo es, se mide con `EXTRACT_CACHE_SIZE=0` (corrida E1).

## ADR-004: El semáforo se adquiere antes de leer el body

**Estado:** aceptada. Se probó lo contrario y se descartó.

**Contexto:** se probó mover la lectura del body, el hash y la consulta del caché fuera del semáforo para que los hits no ocupen slots. Esa versión no está en `main`.

**Resultado:** con la lectura fuera del semáforo, k6 dejó de tener errores de conexión, pero Vegeta perdió el rechazo temprano: los 429 bajaron a 0 y subieron los timeouts. Los resultados están en `docs/benchmarks/E4_cambioA_*` como evidencia negativa.

**Decisión:** el orden se mantiene. El semáforo y su cola acotada van antes de `_read_pdf`. La protección contra cargas grandes se hace con `Content-Length` (ADR no cubre uploads chunked, ver `docs/contratos/extract.md`).

## ADR-005: Errores de PDF inválido como 422, no 400

**Estado:** aceptada.

**Decisión:** un PDF que no se puede abrir (`kind="corrupt"`) o que requiere contraseña (`kind="encrypted"`) devuelve 422. El 400 queda para errores de la petición: falta el campo `file` o no empieza con `%PDF-`.

**Referencia:** `app/infrastructure/pdf_reader.py`, `app/api/v1/endpoints.py` (`except InfraExtractionError`).
