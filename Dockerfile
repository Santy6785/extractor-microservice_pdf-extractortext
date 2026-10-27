FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Copy uv binary from its image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy only lock files first for caching
COPY pyproject.toml uv.lock ./

# Install dependencies in a venv without installing the project itself
RUN uv sync --frozen --no-dev --no-install-project

# Add the application source
COPY app/ ./app

# Ensure the venv is on the PATH
ENV PATH="/app/.venv/bin:$PATH"

# Run the service using uv's runtime (no‑sync because deps are already installed)
CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
