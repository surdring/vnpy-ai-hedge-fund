"""Flow CRUD routes using in-memory storage."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/flows", tags=["flows"])

# In-memory storage
_flows: dict[int, dict] = {}
_next_id: int = 1


@router.get("/")
async def list_flows() -> list[dict]:
    """List all flows."""
    return list(_flows.values())


@router.post("/")
async def create_flow(flow: dict) -> dict:
    """Create a new flow."""
    global _next_id
    flow["id"] = _next_id
    _next_id += 1
    _flows[flow["id"]] = flow
    return flow


@router.put("/{flow_id}")
async def update_flow(flow_id: int, flow: dict) -> dict:
    """Update an existing flow."""
    if flow_id not in _flows:
        raise HTTPException(status_code=404, detail="Flow not found")
    flow["id"] = flow_id
    _flows[flow_id] = flow
    return flow


@router.delete("/{flow_id}")
async def delete_flow(flow_id: int) -> dict:
    """Delete a flow."""
    if flow_id not in _flows:
        raise HTTPException(status_code=404, detail="Flow not found")
    del _flows[flow_id]
    return {"detail": "Flow deleted"}
