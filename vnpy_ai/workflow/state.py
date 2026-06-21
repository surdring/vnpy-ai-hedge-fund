"""
Workflow state types.
"""

from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict):
    """AI Hedge Fund compatible state shape."""

    messages: list[Any]
    data: dict[str, Any]
    metadata: dict[str, Any]

