"""API keys management routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from vnpy_ai_web.backend.database.session import get_db
from vnpy_ai_web.backend.repositories.api_key_repository import ApiKeyRepository

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.get("/")
async def list_api_keys(db: Session = Depends(get_db)) -> list[dict]:  # noqa: B008
    """List all API keys (masked)."""
    repo = ApiKeyRepository(db)
    keys = repo.list_all()
    return [
        {
            "id": k.id,
            "provider": k.provider,
            "key_prefix": k.key_prefix,
            "created_at": k.created_at.isoformat() if k.created_at else None,
        }
        for k in keys
    ]


@router.post("/")
async def create_api_key(data: dict, db: Session = Depends(get_db)) -> dict:  # noqa: B008
    """Create a new API key."""
    repo = ApiKeyRepository(db)
    provider = data.get("provider", "")
    key_prefix = data.get("key_prefix", "")
    encrypted_key = data.get("encrypted_key", "")
    if not provider or not encrypted_key:
        raise HTTPException(status_code=400, detail="provider and encrypted_key are required")
    api_key = repo.create(provider=provider, key_prefix=key_prefix, encrypted_key=encrypted_key)
    return {"id": api_key.id, "provider": api_key.provider, "key_prefix": api_key.key_prefix}


@router.delete("/{api_key_id}")
async def delete_api_key(api_key_id: int, db: Session = Depends(get_db)) -> dict:  # noqa: B008
    """Delete an API key."""
    repo = ApiKeyRepository(db)
    if not repo.delete(api_key_id):
        raise HTTPException(status_code=404, detail="API key not found")
    return {"detail": "API key deleted"}
