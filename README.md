# Extractor PDF → Markdown

Microservicio FastAPI que recibe un PDF y devuelve su texto en Markdown y la cantidad de páginas. Se evalúa con pruebas de carga (k6 y Vegeta).

- Contrato de la API y errores: [`docs/contratos/extract.md`](docs/contratos/extract.md)
- Decisiones de arquitectura: [`docs/decisiones.md`](docs/decisiones.md)
- Informe técnico con benchmarks: [`docs/informe_tecnico.md`](docs/informe_tecnico.md)

## Requisitos

- Docker Desktop (probado con 2,8 GiB de RAM y 8 CPUs)
- PowerShell
- `uv` (solo para correr los tests en el host)

## Modos de despliegue

Hay dos. El modo B publica el puerto 80 del host: si el Traefik externo ya lo usa, no podés levantar los dos a la vez.

### A. Integrado (stack externo de Traefik)

Requiere el Traefik del stack `Documentos\Dockers\Traefik`, unido a la red externa `proxy`.

```powershell
docker network create proxy            # solo la primera vez; si ya existe, da error y se ignora
docker compose up -d --build
docker compose ps                      # esperar a que las 5 réplicas estén (healthy)
```

Dominio local (requiere PowerShell como administrador, una sola vez):

```powershell
Add-Content C:\Windows\System32\drivers\etc\hosts "127.0.0.1 extractor.universidad.localhost"
```

Prueba:

```powershell
curl.exe -k -X POST -H "Content-Type: application/pdf" --data-binary "@tests/stress/pdfs/Filosofia_Lean.pdf" https://extractor.universidad.localhost/extract
```

Traefik solo enruta `/extract` (label `PathPrefix(/extract)` en `docker-compose.yml`).

### B. Standalone (un solo comando, sin red externa)

```powershell
docker compose -f docker-compose.standalone.yml up -d --build
```

Este archivo incluye su propio Traefik en el puerto 80 y enruta `/extract` y `/api/v1/extract` a las 5 réplicas. No necesita crear la red `proxy` ni tener el stack externo.

Prueba:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost/extract -ContentType "application/pdf" -InFile tests\stress\pdfs\Filosofia_Lean.pdf
```

> El perfil `profiles: ["standalone"]` dentro de `docker-compose.yml` no se implementó. En Compose, la red `proxy` declarada como `external: true` se resuelve al cargar el archivo, así que el perfil no evitaría crear la red. Por eso el modo standalone es un archivo aparte.

Para apagar: `docker compose down` (o `docker compose -f docker-compose.standalone.yml down`).

## Tests

```powershell
uv sync
uv run pytest -q -rs
```

Los tests no requieren Docker. Los que usan PDFs reales leen `tests/stress/pdfs/`.

## Pruebas de carga

Se corren dentro de la red Docker, por HTTP, como el profesor. Cambiá `proxy` por `pdf-extractor-standalone` si usás el modo B.

Guardar cada corrida con un nombre distinto. `Tee-Object` sobrescribe el archivo si se reutiliza el nombre.

### k6 (spike, 100 VUs)

```powershell
docker run --rm --network proxy -v "${PWD}/tests/stress:/s" -v "${PWD}/docs/benchmarks:/out" -w /s -e BASE_URL=http://api:80 grafana/k6 run --summary-export=/out/<nombre>.json /s/k6_spike.js 2>&1 | Tee-Object docs\benchmarks\<nombre>.txt
```

Una corrida vale solo si el log llega hasta `TOTAL RESULTS`.

### Vegeta (50 req/s, 30 s, timeout 30 s)

```powershell
docker run --rm --network proxy -v "${PWD}/tests/stress:/s" -v "${PWD}/tests/stress/pdfs:/pdfs" peterevans/vegeta sh -c "vegeta attack -targets=/s/vegeta_targets_docker.txt -rate=50 -duration=30s -timeout=30s | vegeta report" 2>&1 | Tee-Object docs\benchmarks\<nombre>.txt
```

Para medir solo la cola sin caché (E1), levantá con `$env:EXTRACT_CACHE_SIZE = "0"` antes de `docker compose up`.

Antes de cada medición: esperá a que las 5 réplicas estén `(healthy)` y calentá el caché con los 4 PDFs.

## Variables de entorno

Leídas por `app/core/config.py`. Los valores por defecto del código y los del compose no son iguales en dos casos (ver última columna).

| Variable | Default en código | Compose | Qué controla |
|---|---|---|---|
| `PORT` | 80 | — | No lo usa el arranque: el `CMD` del Dockerfile fija `--port 80` |
| `LOG_LEVEL` | `INFO` | — | Nivel de logs JSON a stdout |
| `EXTRACT_CONCURRENCY` | 2 | 3 | Extracciones en paralelo por réplica |
| `EXTRACT_QUEUE_TIMEOUT` | 20 s | 10 s | Espera máxima en la cola antes de 429 |
| `EXTRACT_MAX_QUEUE` | 8 | 8 | Requests esperando en la cola antes de 429 inmediato |
| `EXTRACT_CACHE_SIZE` | 32 | 32 | Entradas del caché por sha256, por réplica (0 lo desactiva) |
| `PDF_MAX_FILE_SIZE_MB` | 50 | 50 | Tamaño máximo del PDF; por encima, 413 |

Para cambiar un valor sin editar archivos: `$env:EXTRACT_CACHE_SIZE = "0"` antes de `docker compose up`.

## URLs y puertos

| Desde | URL |
|---|---|
| Dentro de la red `proxy` (integrado) | `http://api:80/extract` y `http://api:80/api/v1/extract` |
| Host, integrado | `https://extractor.universidad.localhost/extract` |
| Host, standalone | `http://localhost/extract` |

`/api/v1/extract` no pasa por Traefik en el modo integrado. Solo es accesible desde la red Docker (ADR-001).

## Orden de arranque del sistema completo

1. Stack de Traefik y MongoDB (red `proxy` creada).
2. Persistencia.
3. Extractor (este repo).
4. Orquestador.
5. Frontend.

Los puertos de persistencia, orquestador y frontend están en sus propios repos, no en este. Acá no los verificamos.

## Health

`GET /health` devuelve `{"status": "ok"}` de forma fija. **No verifica nada**: no refleja réplicas caídas ni el estado del semáforo.
