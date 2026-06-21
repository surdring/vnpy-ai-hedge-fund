"""
Order adapter from AI decisions to VeighNa OrderRequest objects.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from vnpy.trader.constant import Direction, Offset, OrderType
from vnpy.trader.event import EVENT_ORDER, EVENT_TRADE
from vnpy.trader.object import ContractData, OrderRequest

from .data_adapter import parse_vt_symbol
from .models import PortfolioDecision

logger = logging.getLogger(__name__)


ACTION_MAP: dict[str, tuple[Direction, Offset]] = {
    "buy": (Direction.LONG, Offset.OPEN),
    "sell": (Direction.LONG, Offset.CLOSE),
    "short": (Direction.SHORT, Offset.OPEN),
    "cover": (Direction.SHORT, Offset.CLOSE),
}


@dataclass(frozen=True)
class OrderValidationResult:
    """Validation result for a decision-to-order conversion."""

    ok: bool
    reason: str = ""


class OrderAdapter:
    """Convert portfolio decisions into VeighNa orders."""

    def __init__(self, main_engine: Any | None = None, gateway_name: str = "", order_type: OrderType = OrderType.LIMIT, rpc_bridge: Any | None = None) -> None:
        self.main_engine = main_engine
        self.gateway_name = gateway_name
        self.order_type = order_type
        self._rpc_bridge = rpc_bridge
        self._register_order_callbacks()

    def validate_decision(self, decision: PortfolioDecision) -> OrderValidationResult:
        """Validate an AI decision before order creation."""

        if decision.action == "hold":
            return OrderValidationResult(True)
        if decision.action not in ACTION_MAP:
            return OrderValidationResult(False, f"Unsupported action: {decision.action}")
        if decision.quantity <= 0:
            return OrderValidationResult(False, "Quantity must be positive")
        if decision.price is not None and decision.price < 0:
            return OrderValidationResult(False, "Price must not be negative")

        if self.main_engine and hasattr(self.main_engine, "get_contract"):
            contract = self._get_contract(decision.ticker)
            if contract:
                if contract.min_volume and decision.quantity < contract.min_volume:
                    return OrderValidationResult(False, "Quantity below contract min_volume")
                if contract.max_volume and decision.quantity > contract.max_volume:
                    return OrderValidationResult(False, "Quantity above contract max_volume")

        return OrderValidationResult(True)

    def decision_to_order(self, decision: PortfolioDecision) -> OrderRequest | None:
        """Convert a portfolio decision into an OrderRequest."""

        if decision.action == "hold":
            return None

        validation = self.validate_decision(decision)
        if not validation.ok:
            raise ValueError(validation.reason)

        symbol, exchange = parse_vt_symbol(decision.ticker)
        direction, offset = ACTION_MAP[decision.action]
        return OrderRequest(
            symbol=symbol,
            exchange=exchange,
            direction=direction,
            offset=offset,
            type=self.order_type,
            volume=float(decision.quantity),
            price=float(decision.price or 0),
            reference="vnpy_ai",
        )

    def send_decision(self, decision: PortfolioDecision) -> str:
        """Convert and submit a decision through MainEngine."""

        order = self.decision_to_order(decision)
        if order is None:
            return ""
        if not self.main_engine:
            raise RuntimeError("MainEngine is required to send orders")
        if not self.gateway_name:
            raise RuntimeError("gateway_name is required to send orders")

        # Task 13: position & cash pre-order validation
        try:
            symbol, exchange = parse_vt_symbol(decision.ticker)
            vt_symbol = f"{symbol}.{exchange.value}"

            if decision.action in ("sell", "short"):
                target_dir = Direction.LONG if decision.action == "sell" else Direction.SHORT
                positions = self.main_engine.get_all_positions()
                pos_volume = sum(p.volume for p in positions if p.vt_symbol == vt_symbol and p.direction == target_dir)
                if pos_volume < decision.quantity:
                    logger.warning("Order rejected: insufficient position for %s %s, have %.0f need %d", decision.action, vt_symbol, pos_volume, decision.quantity)
                    return ""

            if decision.action in ("buy", "cover"):
                if decision.price is not None:
                    accounts = self.main_engine.get_all_accounts()
                    available = sum(a.available for a in accounts)
                    estimated_cost = decision.quantity * decision.price
                    if estimated_cost > available:
                        logger.warning("Order rejected: insufficient cash for %s, need %.2f have %.2f", decision.action, estimated_cost, available)
                        return ""
        except Exception:
            pass  # skip validation if position/account data not available

        # Task 14: price range validation
        try:
            if decision.price is not None:
                tick = self.main_engine.get_tick(vt_symbol)
                if tick is not None and tick.last_price > 0:
                    deviation = abs(decision.price - tick.last_price) / tick.last_price
                    if deviation > 0.05:
                        logger.warning("Order rejected: price deviation %.2f%% for %s (decision %.2f vs last %.2f)", deviation * 100, vt_symbol, decision.price, tick.last_price)
                        return ""
        except Exception:
            pass  # skip validation if tick not available

        vt_orderids = self.main_engine.send_order(order, self.gateway_name)
        return vt_orderids[0] if vt_orderids else ""

    def _get_contract(self, ticker: str) -> ContractData | None:
        symbol, exchange = parse_vt_symbol(ticker)
        vt_symbol = f"{symbol}.{exchange.value}"
        if self.main_engine is None:
            return None
        return self.main_engine.get_contract(vt_symbol)

    def _register_order_callbacks(self) -> None:
        """Register for order and trade events to forward via RPC bridge."""
        if self._rpc_bridge is None or self.main_engine is None:
            return
        try:
            event_engine = self.main_engine.event_engine
            event_engine.register(EVENT_ORDER, self._on_order)
            event_engine.register(EVENT_TRADE, self._on_trade)
        except Exception:
            pass

    def _on_order(self, event: Any) -> None:
        """Handle order status updates and forward via RPC."""
        if self._rpc_bridge is None:
            return
        try:
            order = event.data
            self._rpc_bridge.send_message({
                "type": "order_update",
                "data": {
                    "vt_orderid": order.vt_orderid,
                    "status": order.status.value,
                },
            })
        except Exception:
            pass

    def _on_trade(self, event: Any) -> None:
        """Handle trade fill events and forward via RPC."""
        if self._rpc_bridge is None:
            return
        try:
            trade = event.data
            self._rpc_bridge.send_message({
                "type": "order_update",
                "data": {
                    "vt_orderid": trade.vt_orderid,
                    "vt_tradeid": trade.vt_tradeid,
                    "status": "filled",
                },
            })
        except Exception:
            pass
