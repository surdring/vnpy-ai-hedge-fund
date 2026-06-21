"""
Growth Analyst Agent — revenue growth, EPS growth, margin expansion, insider conviction.

Original upstream: ai-hedge-fund/src/agents/growth_agent.py
Copyright (c) Virat Singh, MIT License.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from vnpy_ai.utils.llm import call_llm

from .base import AgentBase


class GrowthAnalystSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: int = Field(ge=0, le=100, description="Confidence 0-100")
    reasoning: str = Field(description="Detailed reasoning")


class GrowthAnalystAgent(AgentBase):
    """Growth Analyst: revenue/EPS growth trends, valuation, margin expansion, insider conviction."""

    agent_id = "growth_analyst_agent"
    agent_name = "Growth Analyst"

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
                    "You are a Growth Analyst specializing in identifying high-growth companies. "
                    "Analyze the stock's growth characteristics:\n\n"
                    "1. Revenue Growth: Analyze historical revenue growth trends and sustainability.\n"
                    "2. Earnings Growth: Examine EPS growth, both historical and projected.\n"
                    "3. Margin Expansion: Is the company improving its operating and net margins?\n"
                    "4. Growth Quality: Is growth organic or acquisition-driven?\n"
                    "5. PEG Ratio: Is the growth reasonably priced?\n"
                    "6. Insider Conviction: Consider insider buying/selling patterns.\n\n"
                    "Signal rules:\n"
                    "- Bullish: Strong, sustainable growth with reasonable valuation\n"
                    "- Bearish: Decelerating growth, margin compression, or excessive valuation\n"
                    "- Neutral: Mixed growth signals or uncertain trajectory\n\n"
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
            pydantic_model=GrowthAnalystSignal,
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


def _default_signal() -> GrowthAnalystSignal:
    return GrowthAnalystSignal(signal="neutral", confidence=50, reasoning="Insufficient data for analysis")


def _neutral_result(ticker: str) -> dict[str, Any]:
    return {
        "agent_id": "growth_analyst_agent",
        "agent_name": "Growth Analyst",
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
        "return_on_equity", "revenue_growth", "earnings_growth",
        "operating_margin", "net_margin", "debt_to_equity",
        "free_cash_flow_yield", "price_to_earnings_ratio",
        "price_to_book_ratio", "earnings_per_share",
        "market_cap",
    ]
    summary = {k: latest.get(k) for k in keys if latest.get(k) is not None}
    return json.dumps(summary, separators=(",", ":"))