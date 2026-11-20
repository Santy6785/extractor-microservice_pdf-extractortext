# Informe técnico: extractor PDF → Markdown

**Materia:** Desarrollo de Software (UTN FRSR), TP de test de carga y stress.
**Fecha:** 2026-11-20.

Todas las cifras de este informe salen de `docs/benchmarks/`. Cada tabla indica el archivo de origen. Las que no están en ese directorio se marcan como tales.

---

## 1. Arquitectura

Un solo endpoint, `POST /extract`, con alias `/api/v1/extract` (ADR-001). Recibe el PDF por multipart o como bytes crudos y devuelve `{"content", "page_count"}` (`docs/contratos/extract.md`).

Capas, de afuera hacia adentro:

1. **Admisión** (`app/api/v1/endpoints.py`): tope de tamaño por `Content-Length` (413), semáforo de `EXTRACT_CONCURRENCY` extracciones por réplica y cola acotada de `EXTRACT_MAX_QUEUE` con timeout `EXTRACT_QUEUE_TIMEOUT`. Lo que no entra recibe 429 con `Retry-After: 1`.
2. **Servicio** (`app/services/extraction.py`): clave sha256 del PDF, consulta al caché LRU (`app/services/cache.py`), extracción y conversión a Markdown.
3. **Infraestructura** (`app/infrastructure/pdf_reader.py`): pymupdf sobre bytes en memoria. Corre en `asyncio.to_thread`.

Despliegue: 5 réplicas con 1 CPU y 1 GiB cada una. Balanceo por Traefik, por labels Docker (`docker-compose.yml`) o en un Traefik propio (`docker-compose.standalone.yml`).

Observabilidad: logs JSON a stdout con `X-Request-ID` (E-06). No se loguea contenido del PDF.

## 2. Qué se mide y con qué carga

Benchmark de la consigna (dato de la consigna, **no está en `docs/benchmarks/`**):

- k6: 100 VUs en spike (10 s subida, 20 s sostenido, 10 s bajada). Referencia: 25,35 req/s, 0% error, mediana 1,88 s.
- Vegeta: 50 req/s durante 30 s, timeout 30 s, rotando los 4 PDFs del dataset. Referencia: 16,65 req/s efectivos, 66,53% de éxito (998/1500), 501 timeouts, mediana 14,89 s.

Los PDFs del dataset pesan entre 0,32 MB y 8,9 MB, con promedio de 3,43 MB. Esto explica el costo de ingestión y no solo el de CPU.

Las mediciones con Vegeta de la tabla 4 se hicieron dentro de la red Docker con HTTP directo (`vegeta_targets_docker.txt`), salvo las filas marcadas como "Windows" (`baseline`, `A`, `B`, `C`), que se corrieron desde el host de Windows. Las notas de sesión no detallan si esas pasaron por Traefik con TLS, así que no lo afirmamos.

## 3. Proceso de investigación

Cada paso cambió una sola variable. Los resultados en el orden en que se obtuvieron:

1. **Librería.** Se comparó pypdf, pypdfium2 y pymupdf (`bench_libs.txt`). pypdf tardó entre 1,3 y 4,9 s por PDF. pypdfium2 fue la más rápida pero devolvió texto desordenado en `Filosofia_Lean.pdf`. pymupdf tardó entre 0,11 y 0,20 s y conservó el orden. Se eligió pymupdf (ADR-002).
2. **Baseline con pypdf** (`baseline_pypdf.txt`): 0,13% de éxito, mediana 9,22 s. Es la línea de partida.
3. **Cambio a pymupdf con semáforo 5 / 0,01 s**, desde Windows (`A_pymupdf_5_001.txt`): 7,87%.
4. **Semáforo 2 / 20 s y 1 / 3 s**, desde Windows (`B_*`, `C_*`): el resultado no mejora. Con cola larga la mediana sube a ~20 s y el éxito cae; con concurrencia 1 y espera de 3 s el éxito queda en ~1%.
5. **Medición dentro de Docker, HTTP directo** (`D_docker_http_5_001_vegeta.txt`): 12,87% de éxito, mediana 2,03 s, 5,74 req/s. El resumen (`D_docker_http_resumen.txt`) cita también un 14,20% de otra corrida, cuyo archivo no está en el repo.
6. **Variaciones de semáforo dentro de Docker** (`D_1_10`, `D_2_10`, `D_3_10`): entre 8,47% y 14,20%. Ninguna configuración de semáforo cambia el resultado de forma sustancial. El cuello de botella no es la admisión sola.
7. **E1: cola acotada sin caché** (`E1_cola_vegeta.txt`, `EXTRACT_CACHE_SIZE=0`): 16,80% de éxito, 7,20 req/s, mediana 312 ms. Es la medición limpia del código final sin caché.
8. **E2: caché por sha256 + cola** (`E2_cache_vegeta.txt`, código final): **86,87% de éxito**, 43,15 req/s, mediana 343,8 ms, p95 1,99 s. Es la mejor medición de Vegeta del repo.
9. **Intento de sacar la lectura del body fuera del semáforo** (Cambio A, descartado, ADR-004): ver sección 6.

## 4. Resultados de Vegeta

Cada fila es una corrida de 1500 requests (50 req/s × 30 s). Fuente: el archivo de la columna final.

| Configuración | Entorno | Éxito | Throughput (req/s) | Mediana | Archivo |
|---|---|---|---|---|---|
| Baseline pypdf, semáforo 5 / 0,01 s | Windows (host) | 0,13% | 0,03 | 9,22 s | `baseline_pypdf.txt` |
| pymupdf, semáforo 5 / 0,01 s | Windows (host) | 7,87% | 3,24 | 197,7 ms | `A_pymupdf_5_001.txt` |
| pymupdf, semáforo 2 / 20 s | Windows (host) | 2,80% | 0,81 | 20,12 s | `B_pymupdf_2_20_vegeta.txt` |
| pymupdf, semáforo 1 / 3 s (3 corridas) | Windows (host) | 0,93% – 1,13% | 0,40 – 0,49 | ~3,09 s | `C_pymupdf_1_3.txt` |
| Docker HTTP, semáforo 5 / 0,01 s | red Docker | 12,87% | 5,74 | 2,03 s | `D_docker_http_5_001_vegeta.txt` |
| Docker HTTP, semáforo 1 / 10 s | red Docker | 8,47% | 2,74 | 10,07 s | `D_1_10_vegeta.txt` |
| Docker HTTP, semáforo 2 / 10 s | red Docker | 8,60% | 2,67 | 11,33 s | `D_2_10_vegeta.txt` |
| Docker HTTP, semáforo 3 / 10 s | red Docker | 14,20% | 4,97 | 10,11 s | `D_3_10_vegeta.txt` |
| **E1: cola sin caché** (código final) | red Docker | 16,80% | 7,20 | 312,4 ms | `E1_cola_vegeta.txt` |
| **E2: caché + cola** (código final) | red Docker | **86,87%** | **43,15** | **343,8 ms** | `E2_cache_vegeta.txt` |
| E4 (Cambio A): caché + cola | red Docker | 31,68% | 7,90 | 30,00 s | `E4_cambioA_cache_vegeta.txt` |
| E4 (Cambio A): cola sin caché | red Docker | 12,32% | 3,07 | 30,00 s | `E4_cambioA_cola_vegeta.txt` |

**Comparación con el profesor (Vegeta):** en E2 el éxito es 86,87% contra 66,53% de referencia, el throughput 43,15 contra 16,65 req/s, y la mediana 343,8 ms contra 14,89 s. Además, E2 tiene 0 timeouts y 195 respuestas 429, mientras la referencia tiene 501 timeouts.

Esta comparación vale solo si el caché por sha256 es admisible para el puntaje. Está pendiente de confirmar con el profesor. Sin caché (E1), el resultado queda en 16,80% de éxito, por debajo de la referencia.

## 5. Resultados de k6

Solo se consideran corridas con resumen completo (`TOTAL RESULTS` en el log o `--summary-export`).

| Configuración | Archivo | Requests | Throughput | Fallos | Mediana |
|---|---|---|---|---|---|
| pymupdf, semáforo 2 / 20 s (Windows) | `B_pymupdf_2_20_k6.txt` | 169 | 3,24 req/s | 49,70% | 18,79 s |
| Docker HTTP, semáforo 2 / 10 s | `D_2_10_k6.txt` | 100 | 1,60 req/s | 56,99% | 24,39 s |
| E4 (Cambio A): caché + cola | `E4_cambioA_cache_k6.txt` y `.json` | 101 | 1,65 req/s | 0,00% | 24,43 s |

Referencia del profesor (consigna): 1037 requests, 25,35 req/s, 0% error, mediana 1,88 s.

**Estado: el k6 no está resuelto.** Ninguna corrida completa del repo se acerca a la referencia del profesor en throughput ni en latencia. La corrida E4 llegó a 0% de fallos, pero a costa de una mediana de 24 s. El resto de las corridas de k6 (`D_1_10`, `D_3_10`, `D_docker_http_5_001`, `E3`, `E4` en texto) se cortaron antes de `TOTAL RESULTS` y no se usan.

**Sobre la corrida de 101 requests con 0% de error:** es la que se describió como "E2 k6". Lo que muestra el archivo es que se midió con el Cambio A (ADR-004), no con el código final. No hay un k6 completo del código final en `docs/benchmarks/`.

**Sobre `E3_cache_cola40_k6.txt`:** no es una medición. Contiene un error de Docker Desktop (HTTP 500 en la API de Docker) y no se usa.

## 6. Análisis

### 6.1 Cuello de botella: ingestión, no solo CPU

Según la nota de medición de la sesión, un PDF cuesta alrededor de 0,3 s de CPU en una réplica caliente. Ese costo no está en `docs/benchmarks/` y no lo verificamos acá. Si se sostiene, la extracción pura con 5 réplicas daría del orden de 16 PDF/s. Los resultados de k6 están por debajo de esa cifra: 1,6 a 3,2 req/s. La diferencia está en subir 3,4 MB por request con 100 VUs en paralelo (k6 registró entre 4,9 y 7,7 MB/s de envío).

### 6.2 El caché es lo que más mueve Vegeta

Pasar de E1 (16,80%) a E2 (86,87%) con el mismo semáforo y la misma cola cambia el resultado. Los hits de caché responden sin extraer; el costo que queda es leer y hashear el PDF. Con 4 PDFs repetidos, la tasa de hits es alta por diseño de la prueba.

### 6.3 Por qué la admisión temprana importa

Los 429 de E2 (195) son rechazos rápidos. Cada uno libera al cliente sin gastar ancho de banda útil. Esto dejó de ser cierto con el Cambio A (ADR-004): al leer el body antes del semáforo, Vegeta pasó de 429 a timeouts (1025 timeouts en E4 cola). Se descartó el cambio.

### 6.4 Medición de CPU con carga de fondo

`E2_docker_stats.txt` tiene 2 muestras (6 s y 18 s). Las réplicas de `api` están entre 1% y 115% de CPU, con 1 CPU por réplica. En la misma muestra aparece el contenedor `cool_brown` con 406% y 446% de CPU, que **no pertenece a este proyecto**. Por eso las muestras no son concluyentes: el host estaba compartido. Hace falta una medición aislada.

## 7. Limitaciones

- **Licencia.** pymupdf es AGPL. Si el proyecto se distribuye, hay que cumplirla.
- **Caché por réplica.** No se comparte entre réplicas. El resultado de E2 depende de que la prueba repita PDFs: con PDFs únicos, el caché no ayuda.
- **Admisión y uploads chunked.** El tope `PDF_MAX_FILE_SIZE_MB` se aplica por `Content-Length` antes de encolar. Un upload chunked sin `Content-Length` se lee completo antes de validar el tamaño.
- **k6 no cumple la referencia.** Ver sección 5. No se publica un k6 del código final porque no existe en el repo.
- **Discrepancia en B.** `B_pymupdf_2_20.txt` (resumen) reporta 3,33% de éxito; `B_pymupdf_2_20_vegeta.txt` reporta 2,80%. Se usa el archivo de Vegeta. No pudimos determinar qué corrida corresponde al resumen.
- **Ruido en el host.** Las mediciones de Docker Desktop comparten CPU con otros contenedores. Hace falta una medición aislada para afirmar un valor de CPU por réplica.
- **Entorno.** Las filas de Windows se ejecutaron desde el host y las de Docker dentro de la red interna por HTTP directo. No son directamente comparables.
- **Health falso.** `/health` devuelve `{"status": "ok"}` fijo.
- **Desvíos de RFC 9457.** `type` repite el path y el `Content-Type` es `application/json` (ver `docs/contratos/extract.md`).

## 8. Evidencia negativa

Estas mediciones no se usan para la configuración final, pero se conservan:

- `E4_cambioA_cache_vegeta.txt`: el Cambio A baja el éxito de E2 de 86,87% a 31,68% con el mismo caché.
- `E4_cambioA_cola_vegeta.txt`: sin caché, el Cambio A baja a 12,32% (E1 era 16,80%).
- `E4_cambioA_cache_k6.*`: el Cambio A da 0% de fallos en k6, pero una mediana de 24 s.

## 9. Reproducibilidad

Los comandos están en `README.md`. El modo standalone levanta todo con `docker compose -f docker-compose.standalone.yml up -d --build`. Las pruebas corren con `uv run pytest -q -rs`.
