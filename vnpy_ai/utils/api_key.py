"""
API key management for the VeighNa AI Hedge Fund integration.

Adapted from ai-hedge-fund/src/utils/api_key.py (MIT License, Virat Singh).
Adds masking helpers so secrets are never leaked to UIs or logs.
"""

from __future__ import annotations

import os
from typing import Any


def get_api_key_from_state(state: dict[str, Any] | None, api_key_name: str) -> str | None:
    """Get an API key from the workflow state's metadata.

    Args:
        state: Workflow state dict (may be None).
        api_key_name: Key name in `request.api_keys`.

    Returns:
        The raw API key string, or None if not found.
    """
    if not state:
        return None
    request = state.get("metadata", {}).get("request")
    if request is None:
        return None
    api_keys = getattr(request, "api_keys", None)
    if not api_keys:
        return None
    value: Any = api_keys.get(api_key_name)
    return str(value) if value is not None else None


def get_api_key_from_env(env_var_name: str) -> str | None:
    """Get an API key from an environment variable.

    Args:
        env_var_name: Environment variable name.

    Returns:
        The raw API key string, or None if unset.
    """
    value = os.environ.get(env_var_name)
    if not value:
        return None
    return value


def mask_api_key(value: str | None) -> str | None:
    """Mask an API key for UI/logging display.

    Returns only the first 3 and last 4 characters with `****` in between.
    Short values (<=7 chars) are fully masked as `****`.

    Args:
        value: Raw API key.

    Returns:
        Masked string safe for display, or None if input is None.
    """
    if value is None:
        return None
    if len(value) <= 7:
        return "****"
    return f"{value[:3]}****{value[-4:]}"


def get_masked_api_key_from_state(
    state: dict[str, Any] | None,
    api_key_name: str,
) -> str | None:
    """Convenience helper: read an API key from state and return it masked."""
    return mask_api_key(get_api_key_from_state(state, api_key_name))
