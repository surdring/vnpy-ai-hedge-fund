"""
Portfolio Manager Agent — final trading decision aggregation.

Original upstream: ai-hedge-fund/src/agents/portfolio_manager.py
Copyright (c) Virat Singh, MIT License.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Literal

from pydantic import BaseModel, Field

from vnpy_ai.agents.base import AgentBase
from vnpy_ai.utils.llm import call_llm
from vnpy_ai.utils.progress import progress

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class PortfolioDecision(BaseModel):
    """Single trading decision for one ticker."""

    action: Literal["buy", "sell", "short", "cover", "hold"]
    quantity: int = Field(ge=0, description="Number of shares to trade")
    confidence: int = Field(ge=0, le=100, description="Confidence 0-100")
    reasoning: str = Field(description="Reasoning for the decision")


class PortfolioManagerOutput(BaseModel):
    """Structured output from the portfolio manager LLM call."""

    decisions: dict[str, PortfolioDecision] = Field(
        description="Dictionary of ticker to trading decisions"
    )


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class PortfolioManagerAgent(AgentBase):
    """Portfolio Manager: aggregates analyst signals, applies risk limits,
    and generates final trading decisions via LLM.
    """

    agent_id = "portfolio_manager_agent"
    agent_name = "Portfolio Manager"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, state: dict[str, Any]) -> dict[str, Any]:
        """Aggregate analyst signals and generate final trading decisions.

        Args:
            state: Workflow state dict with ``data`` and ``metadata`` keys.

        Returns:
            Dict with ``agent_id``, ``agent_name``, ``decisions``, and
            ``portfolio_summary``.
        """
        data = state.get("data", {})
        tickers: list[str] = data.get("tickers", [])
        analyst_signals: dict[str, Any] = data.get("analyst_signals", {})
        portfolio: dict[str, Any] = data.get("portfolio", {})

        if not tickers or not analyst_signals:
            logger.info(
                "Portfolio Manager: no signals or tickers, returning all hold"
            )
            return self._fallback_all_hold(tickers)

        # 1. Aggregate signals by ticker
        signals_by_ticker = self._aggregate_signals(tickers, analyst_signals)

        # 2. Extract risk data (current prices, position limits)
        current_prices = self._extract_current_prices(tickers, analyst_signals)
        position_limits = self._extract_position_limits(tickers, analyst_signals)
        max_shares = self._compute_max_shares(tickers, current_prices, position_limits)

        # 3. Compute deterministic allowed actions
        allowed_actions = self._compute_allowed_actions(
            tickers, current_prices, max_shares, portfolio
        )

        # 4. Pre-fill tickers that can only hold (no valid trade)
        prefilled: dict[str, PortfolioDecision] = {}
        tickers_for_llm: list[str] = []
        for t in tickers:
            aa = allowed_actions.get(t, {"hold": 0})
            if set(aa.keys()) == {"hold"}:
                prefilled[t] = PortfolioDecision(
                    action="hold",
                    quantity=0,
                    confidence=100,
                    reasoning="No valid trade available",
                )
            else:
                tickers_for_llm.append(t)

        # 5. Call LLM for tickers that have actionable options
        if tickers_for_llm:
            progress.update_status(
                self.agent_id, None, "Generating trading decisions"
            )
            llm_decisions = self._generate_llm_decisions(
                tickers_for_llm, signals_by_ticker, allowed_actions, state
            )
        else:
            llm_decisions = {}

        # 6. Merge prefilled + LLM decisions
        merged = {**prefilled, **llm_decisions}

        # 7. Apply hard limits (safety net)
        final = self._apply_hard_limits(merged, tickers, max_shares, portfolio)

        # 8. Build return payload
        decisions_list = [
            {
                "ticker": ticker,
                "action": d.action,
                "quantity": d.quantity,
                "confidence": d.confidence,
                "reasoning": d.reasoning,
            }
            for ticker, d in final.items()
        ]

        summary = self._build_summary(final, signals_by_ticker)

        progress.update_status(self.agent_id, None, "Done")

        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "decisions": decisions_list,
            "portfolio_summary": summary,
        }

    # ------------------------------------------------------------------
    # Fallback
    # ------------------------------------------------------------------

    def _fallback_all_hold(self, tickers: list[str]) -> dict[str, Any]:
        """Return all-hold decisions when no signals are available."""
        decisions = [
            {
                "ticker": t,
                "action": "hold",
                "quantity": 0,
                "confidence": 0,
                "reasoning": "Fallback: no analyst signals available, holding",
            }
            for t in tickers
        ]
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "decisions": decisions,
            "portfolio_summary": {
                "total_signals_analyzed": 0,
                "buy_signals": 0,
                "sell_signals": 0,
                "hold_signals": len(tickers),
            },
        }

    # ------------------------------------------------------------------
    # Signal aggregation
    # ------------------------------------------------------------------

    @staticmethod
    def _aggregate_signals(
        tickers: list[str],
        analyst_signals: dict[str, Any],
    ) -> dict[str, dict[str, dict[str, Any]]]:
        """Aggregate analyst signals keyed by ticker → agent → {sig, conf}.

        Excludes risk_management_agent entries (those hold risk data, not
        trading signals).
        """
        out: dict[str, dict[str, dict[str, Any]]] = {}
        for ticker in tickers:
            ticker_signals: dict[str, dict[str, Any]] = {}
            for agent_key, signals in analyst_signals.items():
                if agent_key.startswith("risk_management_agent"):
                    continue
                if ticker not in signals:
                    continue
                payload = signals[ticker]
                sig = payload.get("signal")
                conf = payload.get("confidence")
                if sig is not None and conf is not None:
                    ticker_signals[agent_key] = {"sig": sig, "conf": conf}
            out[ticker] = ticker_signals
        return out

    # ------------------------------------------------------------------
    # Risk data extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_current_prices(
        tickers: list[str],
        analyst_signals: dict[str, Any],
    ) -> dict[str, float]:
        """Extract current prices from risk management agent data."""
        prices: dict[str, float] = {}
        for ticker in tickers:
            for agent_key, signals in analyst_signals.items():
                if not agent_key.startswith("risk_management_agent"):
                    continue
                risk_data = signals.get(ticker, {})
                price = risk_data.get("current_price")
                if price is not None:
                    prices[ticker] = float(price)
                    break
            else:
                prices[ticker] = 0.0
        return prices

    @staticmethod
    def _extract_position_limits(
        tickers: list[str],
        analyst_signals: dict[str, Any],
    ) -> dict[str, float]:
        """Extract remaining position limits from risk management agent data."""
        limits: dict[str, float] = {}
        for ticker in tickers:
            for agent_key, signals in analyst_signals.items():
                if not agent_key.startswith("risk_management_agent"):
                    continue
                risk_data = signals.get(ticker, {})
                limit = risk_data.get("remaining_position_limit")
                if limit is not None:
                    limits[ticker] = float(limit)
                    break
            else:
                limits[ticker] = 0.0
        return limits

    @staticmethod
    def _compute_max_shares(
        tickers: list[str],
        current_prices: dict[str, float],
        position_limits: dict[str, float],
    ) -> dict[str, int]:
        """Compute max tradeable shares from position limit / price."""
        max_shares: dict[str, int] = {}
        for ticker in tickers:
            price = current_prices.get(ticker, 0.0)
            limit = position_limits.get(ticker, 0.0)
            if price > 0:
                max_shares[ticker] = int(limit // price)
            else:
                max_shares[ticker] = 0
        return max_shares

    # ------------------------------------------------------------------
    # Allowed actions (deterministic constraints)
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_allowed_actions(
        tickers: list[str],
        current_prices: dict[str, float],
        max_shares: dict[str, int],
        portfolio: dict[str, Any],
    ) -> dict[str, dict[str, int]]:
        """Compute allowed actions and max quantities for each ticker."""
        allowed: dict[str, dict[str, int]] = {}
        cash = float(portfolio.get("cash", 0.0))
        positions = portfolio.get("positions", {}) or {}
        margin_requirement = float(portfolio.get("margin_requirement", 0.5))
        margin_used = float(portfolio.get("margin_used", 0.0))
        equity = float(portfolio.get("equity", cash))

        for ticker in tickers:
            price = float(current_prices.get(ticker, 0.0))
            pos = positions.get(
                ticker,
                {"long": 0, "long_cost_basis": 0.0, "short": 0, "short_cost_basis": 0.0},
            )
            long_shares = int(pos.get("long", 0) or 0)
            short_shares = int(pos.get("short", 0) or 0)
            max_qty = int(max_shares.get(ticker, 0) or 0)

            actions: dict[str, int] = {
                "buy": 0,
                "sell": 0,
                "short": 0,
                "cover": 0,
                "hold": 0,
            }

            # Long side
            if long_shares > 0:
                actions["sell"] = long_shares
            if cash > 0 and price > 0:
                max_buy_cash = int(cash // price)
                max_buy = max(0, min(max_qty, max_buy_cash))
                if max_buy > 0:
                    actions["buy"] = max_buy

            # Short side
            if short_shares > 0:
                actions["cover"] = short_shares
            if price > 0 and max_qty > 0:
                if margin_requirement <= 0.0:
                    max_short = max_qty
                else:
                    available_margin = max(
                        0.0, (equity / margin_requirement) - margin_used
                    )
                    max_short_margin = int(available_margin // price)
                    max_short = max(0, min(max_qty, max_short_margin))
                if max_short > 0:
                    actions["short"] = max_short

            # Prune zero-capacity actions (keep hold)
            pruned: dict[str, int] = {"hold": 0}
            for action, qty in actions.items():
                if action != "hold" and qty > 0:
                    pruned[action] = qty

            allowed[ticker] = pruned

        return allowed

    # ------------------------------------------------------------------
    # LLM decision generation
    # ------------------------------------------------------------------

    def _generate_llm_decisions(
        self,
        tickers: list[str],
        signals_by_ticker: dict[str, dict[str, dict[str, Any]]],
        allowed_actions: dict[str, dict[str, int]],
        state: dict[str, Any],
    ) -> dict[str, PortfolioDecision]:
        """Call the LLM to produce trading decisions for actionable tickers."""

        # Compact signals and allowed actions for the LLM prompt
        compact_signals = self._compact_signals(
            {t: signals_by_ticker.get(t, {}) for t in tickers}
        )
        compact_allowed = {t: allowed_actions[t] for t in tickers}

        prompt = (
            "You are a portfolio manager.\n"
            "Inputs per ticker: analyst signals and allowed actions "
            "with max qty (already validated).\n"
            "Pick one allowed action per ticker and a quantity ≤ the max. "
            "Keep reasoning very concise (max 100 chars). "
            "No cash or margin math. Return JSON only.\n\n"
            "Signals:\n"
            f"{json.dumps(compact_signals, separators=(',', ':'), ensure_ascii=False)}\n\n"
            "Allowed:\n"
            f"{json.dumps(compact_allowed, separators=(',', ':'), ensure_ascii=False)}\n\n"
            "Format:\n"
            '{"decisions": {"TICKER": {"action":"...","quantity":int,'
            '"confidence":int,"reasoning":"..."}}}'
        )

        def default_factory() -> PortfolioManagerOutput:
            decisions: dict[str, PortfolioDecision] = {}
            for t in tickers:
                decisions[t] = PortfolioDecision(
                    action="hold",
                    quantity=0,
                    confidence=0,
                    reasoning="Default decision: hold",
                )
            return PortfolioManagerOutput(decisions=decisions)

        try:
            result = call_llm(
                prompt=prompt,
                pydantic_model=PortfolioManagerOutput,
                agent_name=self.agent_id,
                state=state,
                default_factory=default_factory,
            )
        except Exception:
            logger.exception(
                "LLM call failed for portfolio manager; using default hold"
            )
            result = default_factory()

        return result.decisions

    @staticmethod
    def _compact_signals(
        signals_by_ticker: dict[str, dict[str, dict[str, Any]]],
    ) -> dict[str, dict[str, dict[str, Any]]]:
        """Keep only {agent: {sig, conf}} and drop empty agents."""
        out: dict[str, dict[str, dict[str, Any]]] = {}
        for ticker, agents in signals_by_ticker.items():
            if not agents:
                out[ticker] = {}
                continue
            compact: dict[str, dict[str, Any]] = {}
            for agent_key, payload in agents.items():
                sig = payload.get("sig")
                conf = payload.get("conf")
                if sig is not None and conf is not None:
                    compact[agent_key] = {"sig": sig, "conf": conf}
            out[ticker] = compact
        return out

    # ------------------------------------------------------------------
    # Hard limits (safety net)
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_hard_limits(
        decisions: dict[str, PortfolioDecision],
        tickers: list[str],
        max_shares: dict[str, int],
        portfolio: dict[str, Any],
    ) -> dict[str, PortfolioDecision]:
        """Enforce hard limits: no overselling and no exceeding position limits."""
        positions = portfolio.get("positions", {}) or {}
        result: dict[str, PortfolioDecision] = {}

        for ticker in tickers:
            d = decisions.get(ticker)
            if d is None:
                d = PortfolioDecision(
                    action="hold",
                    quantity=0,
                    confidence=0,
                    reasoning="No decision; default hold",
                )

            pos = positions.get(
                ticker,
                {"long": 0, "short": 0},
            )
            long_shares = int(pos.get("long", 0) or 0)
            short_shares = int(pos.get("short", 0) or 0)
            max_qty = max_shares.get(ticker, 0)

            action = d.action
            qty = d.quantity

            if action == "sell":
                qty = min(qty, long_shares)
            elif action == "cover":
                qty = min(qty, short_shares)
            elif action == "buy":
                qty = min(qty, max_qty)
            elif action == "short":
                qty = min(qty, max_qty)

            if qty <= 0 and action != "hold":
                action = "hold"
                qty = 0
                if d.confidence > 0:
                    d = PortfolioDecision(
                        action="hold",
                        quantity=0,
                        confidence=d.confidence,
                        reasoning=f"{d.reasoning} (capped to hold: zero quantity after limits)",
                    )

            result[ticker] = PortfolioDecision(
                action=action,
                quantity=qty,
                confidence=d.confidence,
                reasoning=d.reasoning,
            )

        return result

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    @staticmethod
    def _build_summary(
        decisions: dict[str, PortfolioDecision],
        signals_by_ticker: dict[str, dict[str, dict[str, Any]]],
    ) -> dict[str, int]:
        """Build a summary of the portfolio decisions."""
        total_signals = sum(
            len(agents) for agents in signals_by_ticker.values()
        )
        buy_count = sum(1 for d in decisions.values() if d.action == "buy")
        sell_count = sum(1 for d in decisions.values() if d.action in ("sell", "short"))
        hold_count = sum(1 for d in decisions.values() if d.action == "hold")

        return {
            "total_signals_analyzed": total_signals,
            "buy_signals": buy_count,
            "sell_signals": sell_count,
            "hold_signals": hold_count,
        }