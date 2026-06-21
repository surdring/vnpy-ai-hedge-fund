"""
Agent catalog for the AI Hedge Fund integration.

Original AI Hedge Fund agent implementations are kept in `ai-hedge-fund/`
as the read-only upstream source. This package exposes dependency-light
metadata and fallback execution so VeighNa can start without LangChain.
"""

from .catalog import ANALYST_ORDER, get_agent_catalog, get_agents_list

__all__ = ["ANALYST_ORDER", "get_agent_catalog", "get_agents_list"]

