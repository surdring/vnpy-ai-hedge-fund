"""Ollama routes for model listing and health check."""

from __future__ import annotations

from fastapi import APIRouter

from vnpy_ai_web.backend.services.ollama_service import OllamaService

router = APIRouter(prefix="/ollama", tags=["ollama"])

_service = OllamaService()


@router.get("/models")
async def list_models() -> list[dict]:
    """List available Ollama models."""
    return _service.list_models()


@router.get("/health")
async def health() -> dict:
    """Check Ollama server health."""
    return _service.check_health()
