"""
Progress tracking for the VeighNa AI Hedge Fund integration.

Adapted from ai-hedge-fund/src/utils/progress.py (MIT License, Virat Singh).
Simplified to avoid the optional `rich` dependency; falls back to plain
`print()` output. The public API (AgentProgress, `progress` singleton,
`update_status`, `register_handler`) stays compatible with upstream callers.
"""

from __future__ import annotations

import datetime
from typing import Any
from collections.abc import Callable


class AgentProgress:
    """Track per-agent status updates and notify registered handlers."""

    def __init__(self) -> None:
        self.agent_status: dict[str, dict[str, Any]] = {}
        self.started: bool = False
        self.update_handlers: list[Callable[..., None]] = []

    def register_handler(
        self, handler: Callable[..., None]
    ) -> Callable[..., None]:
        """Register a handler invoked on every status update."""
        self.update_handlers.append(handler)
        return handler

    def unregister_handler(self, handler: Callable[..., None]) -> None:
        """Remove a previously registered handler."""
        if handler in self.update_handlers:
            self.update_handlers.remove(handler)

    def start(self) -> None:
        """Start progress display (no-op in the simplified version)."""
        self.started = True

    def stop(self) -> None:
        """Stop progress display (no-op in the simplified version)."""
        self.started = False

    def update_status(
        self,
        agent_name: str,
        ticker: str | None = None,
        status: str = "",
        analysis: str | None = None,
    ) -> None:
        """Update the status of an agent and notify handlers."""
        if agent_name not in self.agent_status:
            self.agent_status[agent_name] = {"status": "", "ticker": None}

        if ticker:
            self.agent_status[agent_name]["ticker"] = ticker
        if status:
            self.agent_status[agent_name]["status"] = status
        if analysis:
            self.agent_status[agent_name]["analysis"] = analysis

        timestamp = datetime.datetime.now(datetime.UTC).isoformat()
        self.agent_status[agent_name]["timestamp"] = timestamp

        for handler in self.update_handlers:
            try:
                handler(agent_name, ticker, status, analysis, timestamp)
            except Exception:
                # Handler errors must not break the workflow.
                pass

        if self.started and status:
            display_name = self._get_display_name(agent_name)
            ticker_part = f" [{ticker}]" if ticker else ""
            print(f"{display_name}{ticker_part}: {status}")

    def get_all_status(self) -> dict[str, dict[str, Any]]:
        """Return the current status of all agents."""
        return {
            name: {
                "ticker": info.get("ticker"),
                "status": info.get("status"),
                "display_name": self._get_display_name(name),
            }
            for name, info in self.agent_status.items()
        }

    @staticmethod
    def _get_display_name(agent_name: str) -> str:
        """Convert agent_name to a display-friendly format."""
        return agent_name.replace("_agent", "").replace("_", " ").title()


# Global singleton instance, mirroring upstream `progress`.
progress = AgentProgress()
