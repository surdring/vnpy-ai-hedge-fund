"""llama.cpp routes."""

from __future__ import annotations

import requests
from fastapi import APIRouter

router = APIRouter(prefix="/llamacpp", tags=["llamacpp"])

DEFAULT_LLAMA_CPP_URL = "http://localhost:8080"


@router.get("/status")
async def llamacpp_status() -> dict:
    """Check llama.cpp server status and list available models."""
    try:
        resp = requests.get(f"{DEFAULT_LLAMA_CPP_URL}/v1/models", timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            models = [m.get("id", "") for m in data.get("data", [])]
            return {
                "running": True,
                "server_url": DEFAULT_LLAMA_CPP_URL,
                "available_models": models,
            }
        return {
            "running": False,
            "server_url": DEFAULT_LLAMA_CPP_URL,
            "available_models": [],
            "error": f"Server returned status {resp.status_code}",
        }
    except requests.RequestException:
        return {
            "running": False,
            "server_url": DEFAULT_LLAMA_CPP_URL,
            "available_models": [],
        }