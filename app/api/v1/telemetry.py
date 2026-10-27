"""Telemetry routes for the extractor microservice.
Provides `/metrics` and `/trace` endpoints. In a real deployment `/metrics` would expose Prometheus metrics.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/metrics")
async def metrics():
    # Placeholder implementation.
    return JSONResponse(content={"metrics": "not_implemented"})

@router.get("/trace")
async def trace():
    # Minimal trace info – does not return PDF content.
    return JSONResponse(content={"trace": "ok"})
