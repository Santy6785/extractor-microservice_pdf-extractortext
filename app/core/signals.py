"""Estado compartido y manejadores de señales para apagado ordenado del extractor.

Registra manejadores de SIGTERM y SIGINT que:
1. Marcan el servicio como "apagando" para rechazar nuevas extracciones.
2. Esperan a que las extracciones en vuelo finalicen o vencer el tiempo de gracia.
3. Finalizan el proceso limpiamente.
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
import time

logger = logging.getLogger(__name__)

# Estado compartido entre el endpoint de extracción y los manejadores de señal.
_shutting_down = False
_shutdown_started = False
_active_extractions = 0


def is_shutting_down() -> bool:
    """Retorna True si el servicio está en proceso de apagado."""
    return _shutting_down


def set_shutting_down(state: bool) -> None:
    """Establece el flag de apagado."""
    global _shutting_down
    _shutting_down = state


def increment_active_extractions() -> None:
    """Incrementa el contador de extracciones en vuelo."""
    global _active_extractions
    _active_extractions += 1


def decrement_active_extractions() -> None:
    """Decrementa el contador de extracciones en vuelo."""
    global _active_extractions
    _active_extractions = max(0, _active_extractions - 1)


def get_active_extractions() -> int:
    """Retorna el número de extracciones en vuelo."""
    return _active_extractions


async def _drain_and_exit(grace_period_seconds: float = 30.0) -> None:
    """Drena extracciones activas y finaliza el proceso.

    Se invoca ante recepción de SIGTERM/SIGINT. Las extracciones en vuelo
    continúan hasta completarse; las nuevas se rechazan con 503.
    """
    global _shutdown_started

    if _shutdown_started:
        return
    _shutdown_started = True

    set_shutting_down(True)

    deadline = time.monotonic() + grace_period_seconds
    while get_active_extractions() > 0 and time.monotonic() < deadline:
        await asyncio.sleep(0.05)

    remaining = get_active_extractions()
    logger.info(
        "Extractor graceful shutdown complete (remaining_active_extractions=%d)",
        remaining,
    )
    sys.exit(0 if remaining == 0 else 1)


def register_signal_handlers(
    loop: asyncio.AbstractEventLoop,
    grace_period_seconds: float = 30.0,
) -> None:
    """Registra manejadores de SIGTERM y SIGINT en el bucle de eventos."""
    async def _handle_signal() -> None:
        await _drain_and_exit(grace_period_seconds)

    try:
        loop.add_signal_handler(
            signal.SIGTERM, lambda: asyncio.create_task(_handle_signal())
        )
        loop.add_signal_handler(
            signal.SIGINT, lambda: asyncio.create_task(_handle_signal())
        )
        logger.debug("Signal handlers registered for SIGTERM/SIGINT")
    except NotImplementedError:
        logger.debug("Signal handlers not supported on this platform")
    except (ValueError, OSError) as exc:
        logger.warning("Could not register signal handlers: %s", exc)
