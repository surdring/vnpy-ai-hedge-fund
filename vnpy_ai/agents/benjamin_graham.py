"""
Benjamin Graham Agent — classic value investing, net-nets, margin of safety.

Original upstream: ai-hedge-fund/src/agents/ben_graham.py
Copyright (c) Virat Singh, MIT License.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from vnpy_ai.utils.llm import call_llm

from .base import AgentBase


class BenGrahamSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: int = Field(ge=0, le=100, description="Confidence 0-100")
    reasoning: str = Field(description="Detailed reasoning")


class BenjaminGrahamAgent(AgentBase):
    """Benjamin Graham: net-net, Graham Number, conservative balance sheet, margin of safety."""

    agent_id = "ben_graham_agent"
    agent_name = "Ben Graham"

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
                    "You are Benjamin Graham, the father of value investing. Analyze the stock using your principles:\n"
                    "1. Insist on a margin of safety by buying below intrinsic value (Graham Number, net-net).\n"
                    "2. Emphasize financial strength (low leverage, current ratio >= 2.0).\n"
                    "3. Prefer stable earnings over multiple years.\n"
                    "4. Consider dividend record for extra safety.\n"
                    "5. Avoid speculative or high-growth assumptions; focus on proven metrics.\n\n"
                    "Signal rules:\n"
                    "- Bullish: Clear margin of safety, low debt, stable earnings, strong current ratio\n"
                    "- Bearish: Overvalued, high leverage, unstable earnings, poor liquidity\n"
                    "- Neutral: Mixed signals or insufficient margin of safety\n\n"
                    "Confidence scale:\n"
                    "- 90-100: Deep value with >50% margin of safety to Graham Number\n"
                    "- 70-89: Good value with moderate margin of safety\n"
                    "- 50-69: Fair value, limited margin of safety\n"
                    "- 30-49: Slightly overvalued or concerning fundamentals\n"
                    "- 10-29: Significantly overvalued or poor fundamentals\n\n"
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
            pydantic_model=BenGrahamSignal,
            agent_name=self.agent_id,
            state=state,
            default_factory=_default_ben_graham_signal,
        )
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "ticker": ticker,
            "signal": result.signal,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
        }


def _default_ben_graham_signal() -> BenGrahamSignal:
    return BenGrahamSignal(signal="neutral", confidence=50, reasoning="Insufficient data for analysis")


def _neutral_result(ticker: str) -> dict[str, Any]:
    return {
        "agent_id": "ben_graham_agent",
        "agent_name": "Ben Graham",
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
        "return_on_equity", "debt_to_equity", "current_ratio",
        "net_margin", "price_to_earnings_ratio", "price_to_book_ratio",
        "earnings_per_share", "book_value_per_share", "dividend_yield",
        "market_cap", "revenue_growth",
    ]
    summary = {k: latest.get(k) for k in keys if latest.get(k) is not None}
    return json.dumps(summary, separators=(",", ":"))