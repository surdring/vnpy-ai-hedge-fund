"""Workflow graph service - bridges web API to vnpy_ai workflow graph."""

from __future__ import annotations

from typing import Any


def build_graph() -> Any:
    """Build and return the compiled LangGraph workflow graph.

    Delegates to :func:`vnpy_ai.workflow.graph.build_workflow_graph`.
    Returns ``None`` when ``langgraph`` is not installed.
    """
    from vnpy_ai.workflow.graph import build_workflow_graph

    return build_workflow_graph()


def get_graph_info() -> dict[str, Any]:
    """Return the workflow graph topology information.

    Describes the expected node set and edge sequence of the AI Hedge
    Fund workflow graph built by :func:`build_graph`.
    """
    return {
        "nodes": [
            {"id": "analysts", "type": "parallel", "description": "Analyst agents run in parallel"},
            {"id": "risk_manager", "type": "single", "description": "Risk evaluation"},
            {"id": "portfolio_manager", "type": "single", "description": "Portfolio aggregation"},
            {"id": "order_dispatcher", "type": "single", "description": "Order submission"},
            {"id": "status_sync", "type": "single", "description": "Status synchronization"},
        ],
        "edges": [
            {"from": "START", "to": "analysts"},
            {"from": "analysts", "to": "risk_manager"},
            {"from": "risk_manager", "to": "portfolio_manager"},
            {"from": "portfolio_manager", "to": "order_dispatcher"},
            {"from": "order_dispatcher", "to": "status_sync"},
            {"from": "status_sync", "to": "END"},
        ],
    }
