"""Storage status routes."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

router = APIRouter(prefix="/storage", tags=["storage"])


@router.get("/status")
async def storage_status() -> dict:
    """Get storage status information."""
    db_path = Path(__file__).resolve().parent.parent.parent / "vnpy_ai_web.db"
    exists = db_path.exists()
    return {
        "status": "ok" if exists else "not_found",
        "db_path": str(db_path),
        "db_size_bytes": db_path.stat().st_size if exists else 0,
        "type": "sqlite",
    }
