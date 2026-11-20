"""Structured JSON logs to stdout and per-request X-Request-ID.

- Every response carries X-Request-ID (taken from the request if valid, otherwise generated).
- One JSON line per request is logged: method, path, status, duration_ms, request_id.
- Request and response bodies are never logged (PDF content stays out of logs).
"""

from __future__ import annotations

import contextvars
import json
import logging
import re
import sys
import time
import uuid

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")

_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


class JsonFormatter(logging.Formatter):
    """Formats each log record as a single JSON object."""

    _EXTRA_FIELDS = ("method", "path", "status", "duration_ms")

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": getattr(record, "request_id", request_id_var.get()),
        }
        for field in self._EXTRA_FIELDS:
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(level: str = "INFO") -> None:
    """Send all logs to stdout as JSON. Call once at startup."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())


class RequestIdMiddleware:
    """Pure ASGI middleware: X-Request-ID propagation and one access log line per request."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming = dict(scope.get("headers", [])).get(b"x-request-id", b"").decode("latin-1")
        request_id = incoming if _VALID_REQUEST_ID.match(incoming) else uuid.uuid4().hex
        token = request_id_var.set(request_id)
        start = time.perf_counter()
        status_holder = {"code": 500}

        async def send_wrapper(message) -> None:
            if message["type"] == "http.response.start":
                status_holder["code"] = message["status"]
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode("latin-1")))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            logging.getLogger("access").info(
                "request",
                extra={
                    "method": scope["method"],
                    "path": scope["path"],
                    "status": status_holder["code"],
                    "duration_ms": round((time.perf_counter() - start) * 1000, 2),
                    "request_id": request_id,
                },
            )
            request_id_var.reset(token)
