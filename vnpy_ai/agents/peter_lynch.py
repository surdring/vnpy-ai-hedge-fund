"""
Peter Lynch Agent — GARP, PEG ratio, category-based investing.

Original upstream: ai-hedge-fund/src/agents/peter_lynch.py
Copyright (c) Virat Singh, MIT License.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from vnpy_ai.utils.llm import call_llm

from .base import AgentBase


class PeterLynchSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: int = Field(ge=0, le=100, description="Confidence 0-100")
    reasoning: str = Field(description="Detailed reasoning")


class PeterLynchAgent(AgentBase):
    """Peter Lynch: growth at a reasonable price, PEG ratio, invest in what you know."""

    agent_id = "peter_lynch_agent"
    agent_name = "Peter Lynch"

    def analyze(self, state: dict[str, Any]) -> dict[str, Any]:
        ticker = state.get("ticker", "")
        start_date = state.get("start_date", "")
        end_date = state.get("end_date", "")

        try:
            prices = self.get_prices(ticker, start_date, end_date)
            metrics = self.get_financial_metrics(ticker)

            template = ChatPromptTemplate.from_messages([
                (
                    "system",
                    "You are Peter Lynch, legendary Fidelity Magellan fund manager. "
                    "Analyze the stock using your well-known principles:\n"
                    "1. Invest in What You Know: Emphasize understandable businesses.\n"
                    "2. Growth at a Reasonable Price (GARP): Rely on the PEG ratio as a prime metric.\n"
                    "3. Look for 'Ten-Baggers': Companies capable of growing earnings and share price substantially.\n"
                    "4. Steady Growth: Prefer consistent revenue/earnings expansion.\n"
                    "5. Avoid High Debt: Watch for dangerous leverage.\n"
                    "6. Stock Categories: classify as slow-grower, stalwart, fast-grower, cyclical, turnaround, or asset play.\n\n"
                    "In your reasoning:\n"
                    "- Cite the PEG ratio.\n"
                    "- Mention 'ten-bagger' potential if applicable.\n"
                    "- Use practical, folksy language.\n"
                    "- Classify the stock into one of your categories.\n"
                    "- Provide key positives and negatives.\n\n"
                    "Return JSON only."
                ),
                (
                    "human",
                    "Ticker: {ticker}\n"
                    "Price data (last {n_prices} points):\n{prices_summary}\n\n"
                    "Financial metrics (latest):\n{metrics_summary}\n\n"
                    "Return exactly:\n"
                    '{{"signal": "bullish" | "bearish" | "neutral", "confidence": int, "reasoning": "short justification"}}'
                ),
            ])

            prices_summary = _summarize_prices(prices)
            metrics_summary = _summarize_metrics(metrics)

            prompt = template.invoke({
                "ticker": ticker,
                "n_prices": len(prices),
                "prices_summary": prices_summary,
                "metrics_summary": metrics_summary,
            })
        except Exception:
            return _neutral_result(ticker)

        result = call_llm(
            prompt=prompt,
            pydantic_model=PeterLynchSignal,
            agent_name=self.agent_id,
            state=state,
            default_factory=_default_signal,
        )
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "ticker": ticker,
            "signal": result.signal,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
        }


def _default_signal() -> PeterLynchSignal:
    return PeterLynchSignal(signal="neutral", confidence=50, reasoning="Insufficient data for analysis")


def _neutral_result(ticker: str) -> dict[str, Any]:
    return {
        "agent_id": "peter_lynch_agent",
        "agent_name": "Peter Lynch",
        "ticker": ticker,
        "signal": "neutral",
        "confidence": 50,
        "reasoning": "Error fetching data, defaulting to neutral",
    }


def _summarize_prices(prices: list[dict[str, Any]]) -> str:
    if not prices:
        return "No price data available"
    recent = prices[-3:] if len(prices) >= 3 else prices
    return json.dumps([{
        "date": p.get("date", ""),
        "close": p.get("close", "N/A"),
    } for p in recent], separators=(",", ":"))


def _summarize_metrics(metrics: list[dict[str, Any]]) -> str:
    if not metrics:
        return "No financial metrics available"
    latest = metrics[0]
    keys = [
        "return_on_equity", "debt_to_equity", "operating_margin",
        "net_margin", "revenue_growth", "earnings_growth",
        "price_to_earnings_ratio", "price_to_book_ratio",
        "earnings_per_share", "dividend_yield", "free_cash_flow_yield",
        "market_cap",
    ]
    summary = {k: latest.get(k) for k in keys if latest.get(k) is not None}
    return json.dumps(summary, separators=(",", ":"))