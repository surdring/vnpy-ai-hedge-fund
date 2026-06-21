"""LangGraph workflow nodes for vnpy AI integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from vnpy_ai.order_adapter import OrderAdapter


def order_dispatcher(
    state: dict[str, Any],
    order_adapter: OrderAdapter | None = None,
) -> dict[str, Any]:
    """Convert Portfolio Manager decisions to orders via OrderAdapter.

    Args:
        state: Workflow state containing 'data' key with 'decisions' list.
        order_adapter: Optional OrderAdapter instance for sending orders.

    Returns:
        Updated state.
    """
    data = state.get("data", {})
    decisions = data.get("decisions", [])
    if not decisions:
        return {"data": {**data, "order_ids": [], "dispatch_status": "no_decisions"}}

    order_ids = []
    if order_adapter is not None:
        for decision in decisions:
            order_id = order_adapter.send_decision(decision)
            if order_id:
                order_ids.append(order_id)

    return {
        "data": {
            **data,
            "order_ids": order_ids,
            "dispatch_status": "dispatched" if order_ids else "hold_or_skipped",
        }
    }


def status_sync(
    state: dict[str, Any],
    rpc_bridge: Any = None,
) -> dict[str, Any]:
    """Push workflow status to vnpy main process via RPC.

    Args:
        state: Current workflow state.
        rpc_bridge: Optional RpcBridge instance.

    Returns:
        State unchanged (side-effect only).
    """
    data = state.get("data", {})
    status_msg = {
        "status": data.get("workflow_status", "running"),
        "tickers": data.get("tickers", []),
        "decisions": [
            {
                "ticker": d.get("ticker", ""),
                "action": d.get("action", "hold"),
                "confidence": d.get("confidence", 0),
            }
            for d in data.get("decisions", [])
        ],
    }

    if rpc_bridge is not None:
        try:
            rpc_bridge.send_status(status_msg)
        except Exception:
            pass  # Non-critical; don't block workflow

    return {"data": {**data, "status_synced": True}}


def fallback_handler(
    state: dict[str, Any],
) -> dict[str, Any]:
    """Fallback handler when LLM is unavailable.

    Generates hold decisions for all tickers with confidence=0.

    Args:
        state: Workflow state with 'data' key containing 'tickers'.

    Returns:
        Updated state with fallback hold decisions.
    """
    data = state.get("data", {})
    tickers = data.get("tickers", [])
    decisions = [
        {
            "ticker": ticker,
            "action": "hold",
            "confidence": 0,
            "reasoning": "LLM unavailable; fallback to hold (degraded)",
        }
        for ticker in tickers
    ]
    return {
        "data": {
            **data,
            "decisions": decisions,
            "workflow_status": "degraded_fallback",
            "analyst_signals": {},
        }
    }
