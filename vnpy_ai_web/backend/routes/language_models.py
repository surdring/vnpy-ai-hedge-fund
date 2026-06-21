"""Language models routes."""

from __future__ import annotations

from fastapi import APIRouter

from vnpy_ai.config import mask_api_keys

router = APIRouter(prefix="/language-models", tags=["language-models"])


@router.get("/")
async def language_models() -> dict[str, list[dict[str, str]]]:
    """List available language models."""
    return {
        "models": [
            {"display_name": "Ollama llama3", "model_name": "llama3", "provider": "Ollama"},
        ]
    }


@router.post("/mask")
async def mask_keys(api_keys: dict[str, str]) -> dict[str, str]:
    """Mask API keys for safe display."""
    return mask_api_keys(api_keys)
