"""
Workflow runner with a no-LLM fallback path.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, cast

from .state import AgentState
from ..data_adapter import DataAdapter
from ..event_adapter import EventAdapter
from ..models import PortfolioDecision, WorkflowResult


DEFAULT_ANALYSTS = [
    "aswath_damodaran",
    "ben_graham",
    "bill_ackman",
    "cathie_wood",
    "charlie_munger",
    "michael_burry",
    "mohnish_pabrai",
    "nassim_taleb",
    "peter_lynch",
    "phil_fisher",
    "rakesh_jhunjhunwala",
    "stanley_druckenmiller",
    "warren_buffett",
    "technical_analyst",
    "fundamentals_analyst",
    "growth_analyst",
    "news_sentiment_analyst",
    "sentiment_analyst",
    "valuation_analyst",
]


def create_initial_state(
    tickers: list[str],
    portfolio: dict[str, Any],
    start_date: str | None = None,
    end_date: str | None = None,
    model_name: str = "llama3",
    model_provider: str = "Ollama",
) -> AgentState:
    """Create workflow state compatible with the original AI Hedge Fund shape."""

    end = end_date or datetime.now().date().isoformat()
    start = start_date or (datetime.fromisoformat(end) - timedelta(days=90)).date().isoformat()
    return {
        "messages": [],
        "data": {
            "tickers": tickers,
            "portfolio": portfolio,
            "start_date": start,
            "end_date": end,
            "analyst_signals": {},
        },
        "metadata": {
            "show_reasoning": False,
            "model_name": model_name,
            "model_provider": model_provider,
        },
    }


class WorkflowRunner:
    """Run the AI workflow, falling back to deterministic hold decisions."""

    def __init__(
        self,
        data_adapter: DataAdapter,
        selected_analysts: list[str] | None = None,
        event_adapter: EventAdapter | None = None,
        fallback_strategy: str = "hold",
    ) -> None:
        self.data_adapter = data_adapter
        self.selected_analysts = selected_analysts or DEFAULT_ANALYSTS
        self._event_adapter = event_adapter
        self.fallback_strategy = fallback_strategy

    def _run_sma_cross_fallback(
        self, tickers: list[str], current_prices: dict[str, float]
    ) -> dict[str, PortfolioDecision]:
        """Run SMA crossover fallback strategy.

        Uses numpy if available to compute SMA(5) and SMA(20) from price history.
        Falls back to hold if numpy is not available.
        """
        try:
            import numpy as np
        except ImportError:
            return {
                ticker: PortfolioDecision(
                    ticker=ticker,
                    action="hold",
                    quantity=0,
                    confidence=0,
                    reasoning="numpy unavailable; sma_cross fallback degraded to hold",
                    price=current_prices.get(ticker),
                )
                for ticker in tickers
            }

        decisions: dict[str, PortfolioDecision] = {}
        for ticker in tickers:
            prices = self.data_adapter.get_prices(
                ticker,
                cast(str, None),
                cast(str, None),
            )
            if prices and len(prices) >= 20:
                closes = np.array([p.close for p in prices])
                sma5 = np.mean(closes[-5:])
                sma20 = np.mean(closes[-20:])
                if sma5 > sma20:
                    action = "buy"
                    reasoning = f"SMA(5)={sma5:.2f} > SMA(20)={sma20:.2f}; sma_cross fallback signal"
                elif sma5 < sma20:
                    action = "sell"
                    reasoning = f"SMA(5)={sma5:.2f} < SMA(20)={sma20:.2f}; sma_cross fallback signal"
                else:
                    action = "hold"
                    reasoning = f"SMA(5)={sma5:.2f} = SMA(20)={sma20:.2f}; sma_cross fallback signal"
            else:
                action = "hold"
                reasoning = "insufficient price history for sma_cross fallback"

            decisions[ticker] = PortfolioDecision(
                ticker=ticker,
                action=cast(Any, action),
                quantity=0,
                confidence=0,
                reasoning=reasoning,
                price=current_prices.get(ticker),
            )

        return decisions

    def run(
        self,
        tickers: list[str],
        portfolio: dict[str, Any] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        model_name: str = "llama3",
        model_provider: str = "Ollama",
    ) -> WorkflowResult:
        """Run workflow or fallback when optional LangGraph dependencies are absent."""

        if self._event_adapter is not None:
            self._event_adapter.publish_status(status="start", progress=0, message="Starting workflow...")

        portfolio_data = portfolio or self.data_adapter.get_portfolio(tickers)
        state = create_initial_state(tickers, portfolio_data, start_date, end_date, model_name, model_provider)

        current_prices: dict[str, float] = {}
        for ticker in tickers:
            prices = self.data_adapter.get_prices(ticker, state["data"]["start_date"], state["data"]["end_date"])
            if prices:
                current_prices[ticker] = prices[-1].close

        if self._event_adapter is not None:
            self._event_adapter.publish_status(status="progress", progress=50, message="Analyzing...")

        # Try to use LangGraph workflow
        try:
            from .graph import build_workflow_graph

            graph = build_workflow_graph()
            if graph is not None:
                result = graph.invoke(state)
                result_data = result.get("data", {})
                decisions_dict: dict[str, PortfolioDecision] = {}
                for d in result_data.get("decisions", []):
                    ticker = d.get("ticker", "")
                    price = current_prices.get(ticker)
                    decisions_dict[ticker] = PortfolioDecision(
                        ticker=ticker,
                        action=d.get("action", "hold"),
                        quantity=d.get("quantity", 0),
                        confidence=d.get("confidence", 0),
                        reasoning=d.get("reasoning", ""),
                        price=price,
                    )
                return WorkflowResult(
                    decisions=decisions_dict,
                    analyst_signals=result_data.get("analyst_signals", {}),
                    current_prices=current_prices,
                    degraded=result_data.get("workflow_status") == "degraded_fallback",
                )
        except Exception:
            import logging

            logging.getLogger(__name__).warning("LangGraph workflow failed, falling back to hold", exc_info=True)

        # Fallback: use configured fallback strategy
        if self.fallback_strategy == "sma_cross":
            decisions = self._run_sma_cross_fallback(tickers, current_prices)
        else:
            decisions = {
                ticker: PortfolioDecision(
                    ticker=ticker,
                    action="hold",
                    quantity=0,
                    confidence=0,
                    reasoning="LLM unavailable or disabled; degraded fallback strategy holds position",
                    price=current_prices.get(ticker),
                )
                for ticker in tickers
            }

        if self._event_adapter is not None:
            self._event_adapter.publish_status(status="complete", progress=100, message="Workflow complete")

        return WorkflowResult(
            decisions=decisions,
            analyst_signals={},
            current_prices=current_prices,
            degraded=True,
        )


def get_agents_list() -> list[dict[str, Any]]:
    """Return analyst metadata for Web/UI selectors without importing LangChain."""

    return [
        {
            "key": key,
            "display_name": key.replace("_", " ").title(),
            "description": "AI Hedge Fund analyst",
            "investing_style": "Configured analyst workflow",
            "order": index,
        }
        for index, key in enumerate(DEFAULT_ANALYSTS)
    ]
