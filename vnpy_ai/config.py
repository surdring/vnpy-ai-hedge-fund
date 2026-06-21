"""
Configuration loading for the AI integration.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "default_settings.json"


class AiSettings(BaseModel):
    """Runtime settings for the AI integration."""

    enabled: bool = False
    enable_auto_trading: bool = False
    trigger_frequency: str = "daily"
    selected_analysts: list[str] = Field(default_factory=list)
    llm_model_name: str = "llama3"
    llm_provider: str = "Ollama"
    max_position_ratio: float = 0.2
    signal_cooldown: int = 60
    fallback_strategy: str = "hold"
    rpc_host: str = "127.0.0.1"
    rpc_server_port: int = 9001
    rpc_agent_port: int = 9002
    gateway_name: str = ""
    order_type: str = "LIMIT"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid settings file: {path}")
    return data


def load_settings(path: str | Path | None = None) -> AiSettings:
    """Load settings from JSON and environment variables."""

    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    data = _read_json(config_path)

    env_map: dict[str, tuple[str, type]] = {
        "AI_AGENT_ENABLED": ("enabled", bool),
        "AI_AGENT_AUTO_TRADE": ("enable_auto_trading", bool),
        "AI_AGENT_TRIGGER_FREQUENCY": ("trigger_frequency", str),
        "AI_AGENT_SELECTED_ANALYSTS": ("selected_analysts", list),
        "AI_AGENT_MODEL_NAME": ("llm_model_name", str),
        "AI_AGENT_MODEL_PROVIDER": ("llm_provider", str),
        "RPC_SERVER_PORT": ("rpc_server_port", int),
        "RPC_AGENT_PORT": ("rpc_agent_port", int),
    }

    for env_name, (field_name, field_type) in env_map.items():
        value = os.getenv(env_name)
        if value is None:
            continue
        if field_type is bool:
            data[field_name] = value.lower() in {"1", "true", "yes", "on"}
        elif field_type is int:
            data[field_name] = int(value)
        elif field_type is list:
            data[field_name] = [item.strip() for item in value.split(",") if item.strip()]
        else:
            data[field_name] = value

    return AiSettings(**data)


def mask_api_keys(api_keys: dict[str, str]) -> dict[str, str]:
    """Return masked API keys for frontend responses."""

    from .models import mask_secret

    return {provider: mask_secret(value) or "" for provider, value in api_keys.items()}

