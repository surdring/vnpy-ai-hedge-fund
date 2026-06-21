"""Flow runs routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from vnpy_ai_web.backend.database.session import get_db
from vnpy_ai_web.backend.repositories.flow_run_repository import FlowRunRepository

router = APIRouter(prefix="/flow-runs", tags=["flow-runs"])


@router.get("/")
async def list_flow_runs(flow_id: int | None = None, db: Session = Depends(get_db)) -> list[dict]:  # noqa: B008
    """List flow runs, optionally filtered by flow_id."""
    repo = FlowRunRepository(db)
    if flow_id is not None:
        runs = repo.list_by_flow(flow_id)
    else:
        runs = repo.list_all()
    return [
        {
            "id": r.id,
            "flow_id": r.flow_id,
            "status": r.status,
            "result": r.result,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        }
        for r in runs
    ]


@router.get("/{run_id}")
async def get_flow_run(run_id: int, db: Session = Depends(get_db)) -> dict:  # noqa: B008
    """Get a specific flow run by ID."""
    repo = FlowRunRepository(db)
    run = repo.get_by_id(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Flow run not found")
    return {
        "id": run.id,
        "flow_id": run.flow_id,
        "status": run.status,
        "result": run.result,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }
