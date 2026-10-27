"""Admin routes for lifecycle control (pause, resume, shutdown).\nThese endpoints are intended for the orchestrator and are not exposed publicly via Traefik.\nThey operate on an in‑memory service state.\n"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter()

# Simple global state (for demonstration only)
_state = {
    "running": True,
    "paused": False,
    "shutting_down": False,
}

@router.post("/pause")
async def pause_service():
    if not _state["running"]:
        raise HTTPException(status_code=400, detail="Service not running")
    _state["paused"] = True
    return JSONResponse(content={"status": "paused"})

@router.post("/resume")
async def resume_service():
    if not _state["running"]:
        raise HTTPException(status_code=400, detail="Service not running")
    _state["paused"] = False
    return JSONResponse(content={"status": "running"})

@router.post("/shutdown")
async def shutdown_service():
    _state["running"] = False
    _state["shutting_down"] = True
    return JSONResponse(content={"status": "shutting_down"})

@router.get("/metrics")
async def metrics():
    # Placeholder – in a real service you would expose Prometheus metrics.
    return JSONResponse(content={"metrics": "not_implemented"})

@router.get("/trace")
async def trace():
    # Minimal trace info – no PDF bytes returned.
    return JSONResponse(content={"trace": "ok"})
