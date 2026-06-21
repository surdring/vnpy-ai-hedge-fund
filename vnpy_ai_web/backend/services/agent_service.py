"""Agent service - provides agent metadata and execution."""

from __future__ import annotations

from typing import Any


class AgentService:
    """Service for querying AI Hedge Fund agent metadata.

    Bridges the web API to :mod:`vnpy_ai.agents.catalog` and
    :mod:`vnpy_ai.workflow.runner` without importing heavy optional
    dependencies at module load time.
    """

    def list_agents(self) -> list[dict[str, Any]]:
        """Return the list of available agents.

        Prefers :func:`vnpy_ai.workflow.runner.get_agents_list` and falls
        back to :func:`vnpy_ai.agents.catalog.get_agents_list` when the
        workflow module cannot be imported.
        """
        try:
            from vnpy_ai.workflow.runner import get_agents_list
        except ImportError:
            from vnpy_ai.agents.catalog import get_agents_list
        return get_agents_list()

    def get_agent(self, agent_key: str) -> dict[str, Any] | None:
        """Return metadata for a single agent by key, or None if not found."""
        try:
            from vnpy_ai.agents.catalog import get_agent_catalog
        except ImportError:
            return None
        catalog = get_agent_catalog()
        return catalog.get(agent_key)
