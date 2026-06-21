"""LangGraph workflow graph for AI Hedge Fund."""

from __future__ import annotations

from typing import Any
import logging

logger = logging.getLogger(__name__)


def build_workflow_graph(
    agents: list[Any] | None = None,
    order_adapter: Any = None,
    rpc_bridge: Any = None,
    risk_manager_agent: Any = None,
    portfolio_manager_agent: Any = None,
    data_adapter: Any = None,
) -> Any:
    """Build the LangGraph StateGraph for the AI Hedge Fund workflow.

    Topology:
        Start -> Analyst Agents (parallel) -> Risk Manager -> Portfolio Manager
        -> OrderDispatcher -> StatusSync -> End

    If langgraph is not installed, returns None.

    Args:
        agents: List of analyst agent instances.
        order_adapter: Optional OrderAdapter for order submission.
        rpc_bridge: Optional RpcBridge for status sync.
        risk_manager_agent: Optional RiskManagerAgent instance (auto-created if None).
        portfolio_manager_agent: Optional PortfolioManagerAgent instance (auto-created if None).
        data_adapter: Optional DataAdapter for agent data fetching (needed for auto-creation).

    Returns:
        Compiled LangGraph graph, or None if langgraph unavailable.
    """
    try:
        from langgraph.graph import StateGraph, END
    except ImportError:
        logger.warning("langgraph not installed; workflow graph disabled")
        return None

    from vnpy_ai.workflow.state import AgentState

    agents = agents or []

    # Lazy-import nodes; fall back to inline implementations if nodes.py missing
    _nodes = _get_node_functions(order_adapter, rpc_bridge)

    # --- Auto-create RiskManagerAgent if not provided ---
    if risk_manager_agent is None and data_adapter is not None:
        try:
            from vnpy_ai.agents.risk_manager import RiskManagerAgent

            risk_manager_agent = RiskManagerAgent(data_adapter)
            logger.debug("RiskManagerAgent auto-created")
        except ImportError:
            logger.debug("RiskManagerAgent not available; using inline fallback")

    # --- Auto-create PortfolioManagerAgent if not provided ---
    if portfolio_manager_agent is None and data_adapter is not None:
        try:
            from vnpy_ai.agents.portfolio_manager import PortfolioManagerAgent

            portfolio_manager_agent = PortfolioManagerAgent(data_adapter)
            logger.debug("PortfolioManagerAgent auto-created")
        except ImportError:
            logger.debug("PortfolioManagerAgent not available; using inline fallback")

    # Build the graph
    workflow = StateGraph(AgentState)

    # Add analyst agent nodes (one per agent)
    for agent in agents:
        agent_id = getattr(agent, "agent_id", agent.__class__.__name__)
        workflow.add_node(agent_id, agent.analyze)

    # Add risk and portfolio manager nodes (real agents or fallback placeholders)
    if risk_manager_agent is not None:
        workflow.add_node("risk_manager", risk_manager_agent.analyze)
    else:
        workflow.add_node("risk_manager", _make_risk_manager_node())

    if portfolio_manager_agent is not None:
        workflow.add_node("portfolio_manager", portfolio_manager_agent.analyze)
    else:
        workflow.add_node("portfolio_manager", _make_portfolio_manager_node())

    # Add vnpy integration nodes
    workflow.add_node("order_dispatcher", _nodes["order_dispatcher"])
    workflow.add_node("status_sync", _nodes["status_sync"])
    workflow.add_node("fallback_handler", _nodes["fallback_handler"])

    # Set entry point and edges
    if agents:
        workflow.set_entry_point(_get_agent_id(agents[0]))
        # Fan-in: all analysts connect to risk_manager
        for agent in agents:
            workflow.add_edge(_get_agent_id(agent), "risk_manager")
    else:
        workflow.set_entry_point("fallback_handler")
        workflow.add_edge("fallback_handler", END)
        return workflow.compile()

    # Connect risk -> portfolio -> order_dispatcher -> status_sync -> END
    workflow.add_edge("risk_manager", "portfolio_manager")
    workflow.add_edge("portfolio_manager", "order_dispatcher")
    workflow.add_edge("order_dispatcher", "status_sync")
    workflow.add_edge("status_sync", END)

    return workflow.compile()


def _get_agent_id(agent: Any) -> str:
    """Extract agent identifier from an agent instance."""
    return str(getattr(agent, "agent_id", agent.__class__.__name__))


def _get_node_functions(
    order_adapter: Any,
    rpc_bridge: Any,
) -> dict[str, Any]:
    """Resolve node functions from nodes.py or use inline fallbacks."""

    try:
        from vnpy_ai.workflow.nodes import (  # type: ignore[import-not-found]
            order_dispatcher,
            status_sync,
            fallback_handler,
        )

        return {
            "order_dispatcher": lambda state: order_dispatcher(state, order_adapter),
            "status_sync": lambda state: status_sync(state, rpc_bridge),
            "fallback_handler": fallback_handler,
        }
    except ImportError:
        logger.debug("vnpy_ai.workflow.nodes not found; using inline fallback nodes")

        # --- Inline fallback: order_dispatcher ---
        def _order_dispatcher(state: dict[str, Any]) -> dict[str, Any]:
            """Fallback: log decisions, no real order submission."""
            data = state.get("data", {})
            decisions = data.get("decisions", [])
            logger.info("OrderDispatcher fallback: %d decision(s) queued", len(decisions))
            for d in decisions:
                logger.info(
                    "  %s → %s (confidence=%.2f)",
                    d.get("ticker", "?"),
                    d.get("action", "hold"),
                    d.get("confidence", 0),
                )
            data = {**data, "orders_dispatched": True, "workflow_status": "orders_dispatched"}
            return {"data": data}

        # --- Inline fallback: status_sync ---
        def _status_sync(state: dict[str, Any]) -> dict[str, Any]:
            """Fallback: sync workflow status (no-op if no rpc_bridge)."""
            data = state.get("data", {})
            if rpc_bridge is not None:
                try:
                    rpc_bridge.send_status(data.get("workflow_status", "unknown"))
                except Exception:
                    logger.debug("RPC status sync skipped", exc_info=True)
            data = {**data, "status_synced": True}
            return {"data": data}

        # --- Inline fallback: fallback_handler ---
        def _fallback_handler(state: dict[str, Any]) -> dict[str, Any]:
            """Fallback: mark workflow as degraded."""
            logger.warning("Workflow entering fallback handler")
            data = state.get("data", {})
            tickers = data.get("tickers", [])
            decisions = [
                {
                    "ticker": t,
                    "action": "hold",
                    "confidence": 0,
                    "reasoning": "Fallback: hold — no analyst signals available",
                }
                for t in tickers
            ]
            data = {
                **data,
                "decisions": decisions,
                "workflow_status": "degraded",
            }
            return {"data": data}

        return {
            "order_dispatcher": _order_dispatcher,
            "status_sync": _status_sync,
            "fallback_handler": _fallback_handler,
        }


def _make_risk_manager_node() -> Any:
    """Create a fallback risk manager node.

    This is a downgrade path used only when RiskManagerAgent is unavailable
    (e.g., missing dependencies like numpy/pandas, or import errors).
    It passes through all signals without real risk evaluation.
    """

    def risk_manager(state: dict[str, Any]) -> dict[str, Any]:
        """Fallback: evaluate risk for each analyst signal (pass-through)."""
        data = state.get("data", {})
        signals = data.get("analyst_signals", {})

        if not signals:
            logger.info("Risk manager: no signals to evaluate, routing to fallback")
            data = {**data, "workflow_status": "risk_no_signals"}
            return {"data": data}

        # For now, pass through all signals (risk evaluation to be implemented)
        return {
            "data": {
                **data,
                "risk_assessments": {},
                "workflow_status": "risk_evaluated",
            }
        }

    return risk_manager


def _make_portfolio_manager_node() -> Any:
    """Create a fallback portfolio manager node.

    This is a downgrade path used only when PortfolioManagerAgent is unavailable
    (e.g., missing dependencies like pydantic, or import errors).
    It returns all-hold decisions without any LLM-based aggregation.
    """

    def portfolio_manager(state: dict[str, Any]) -> dict[str, Any]:
        """Fallback: aggregate analyst signals into final decisions (hold-only)."""
        data = state.get("data", {})
        signals = data.get("analyst_signals", {})

        if not signals:
            logger.info("Portfolio manager: no signals, routing to fallback")
            data = {**data, "workflow_status": "portfolio_no_signals"}
            return {"data": data}

        # For now, return hold decisions (portfolio management to be implemented)
        tickers = data.get("tickers", [])
        decisions = [
            {
                "ticker": t,
                "action": "hold",
                "confidence": 0,
                "reasoning": "Portfolio manager not yet implemented with LLM; hold",
            }
            for t in tickers
        ]
        return {
            "data": {
                **data,
                "decisions": decisions,
                "workflow_status": "decisions_ready",
            }
        }

    return portfolio_manager
