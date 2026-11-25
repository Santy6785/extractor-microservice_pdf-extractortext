"""Pruebas de graceful shutdown para el microservicio Extractor.

Verifica que:
1. El manejador de señales marca el servicio como apagando.
2. El endpoint /extract rechaza nuevas extracciones con 503 durante el apagado.
3. El contador de extracciones activas se incrementa y decrementa correctamente.
4. register_signal_handlers es invocable sin errores.
"""

from __future__ import annotations

from unittest.mock import patch

import asyncio

from fastapi.testclient import TestClient

from app.api.v1.endpoints import is_shutting_down
from app.core.signals import (
    register_signal_handlers,
    set_shutting_down,
    increment_active_extractions,
    decrement_active_extractions,
    get_active_extractions,
)
from app.main import app


def _reset_state() -> None:
    set_shutting_down(False)
    import app.api.v1.endpoints as ep

    ep._esperando = 0
    while ep._semaphore.locked():
        ep._semaphore.release()


def test_signal_sets_shutting_down_flag():
    """Verifica que set_shutting_down(True) activa el flag de apagado."""
    _reset_state()
    try:
        assert is_shutting_down() is False
        set_shutting_down(True)
        assert is_shutting_down() is True
    finally:
        _reset_state()


def test_middleware_blocks_new_extractions_when_shutting_down():
    """Verifica que /extract devuelve 503 cuando el servicio está apagando."""
    _reset_state()
    try:
        set_shutting_down(True)

        client = TestClient(app)

        response = client.post(
            "/extract",
            content=b"%PDF-1.4 fake pdf content",
            headers={"Content-Type": "application/pdf"},
        )

        assert response.status_code == 503
        body = response.json()
        assert body["title"] == "Service Unavailable"
    finally:
        _reset_state()


def test_active_extractions_counter():
    """Verifica que el contador de extracciones activas se maneja correctamente."""
    _reset_state()
    try:
        assert get_active_extractions() == 0

        increment_active_extractions()
        assert get_active_extractions() == 1

        increment_active_extractions()
        assert get_active_extractions() == 2

        decrement_active_extractions()
        assert get_active_extractions() == 1

        decrement_active_extractions()
        assert get_active_extractions() == 0

        # No debe bajar de cero
        decrement_active_extractions()
        assert get_active_extractions() == 0
    finally:
        _reset_state()


def test_register_signal_handlers_callable():
    """Verifica que register_signal_handlers es invocable sin errores."""
    loop = asyncio.new_event_loop()
    try:
        register_signal_handlers(loop, grace_period_seconds=30.0)
    finally:
        loop.close()


def test_shutting_down_persists_across_calls():
    """Verifica que el flag de apagado se mantiene entre llamadas."""
    _reset_state()
    try:
        set_shutting_down(True)
        assert is_shutting_down() is True
        assert is_shutting_down() is True  # sigue True en siguiente llamada
    finally:
        _reset_state()
