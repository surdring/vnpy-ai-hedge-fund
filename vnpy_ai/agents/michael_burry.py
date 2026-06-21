"""
Michael Burry Agent — deep value, contrarian, balance sheet focus, hard catalysts.

Original upstream: ai-hedge-fund/src/agents/michael_burry.py
Copyright (c) Virat Singh, MIT License.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from vnpy_ai.utils.llm import call_llm

from .base import AgentBase


class MichaelBurrySignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: int = Field(ge=0, le=100, description="Confidence 0-100")
    reasoning: str = Field(description="Detailed reasoning")


class MichaelBurryAgent(AgentBase):
    """Michael Burry: deep value, contrarian, FCF yield, EV/EBIT, insider buying catalysts."""

    agent_id = "michael_burry_agent"
    agent_name = "Michael Burry"

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
                    "You are an AI agent emulating Dr. Michael J. Burry. Your mandate:\n"
                    "- Hunt for deep value in equities using hard numbers (free cash flow, EV/EBIT, balance sheet).\n"
                    "- Be contrarian: hatred in the press can be your friend if fundamentals are solid.\n"
                    "- Focus on downside first – avoid leveraged balance sheets.\n"
                    "- Look for hard catalysts such as insider buying, buybacks, or asset sales.\n"
                    "- Communicate in Burry's terse, data-driven style.\n\n"
                    "When providing your reasoning:\n"
                    "1. Start with the key metric(s) that drove your decision.\n"
                    "2. Cite concrete numbers (e.g., 'FCF yield 14.7%', 'EV/EBIT 5.3').\n"
                    "3. Highlight risk factors and why they are acceptable (or not).\n"
                    "4. Use Burry's direct, number-focused communication style with minimal words.\n\n"
                    "Signal rules:\n"
                    "- Bullish: Deep value with high FCF yield, low leverage, and catalyst present\n"
                    "- Bearish: Overvalued, high leverage, or deteriorating fundamentals\n"
                    "- Neutral: Mixed signals or insufficient data\n\n"
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
            pydantic_model=MichaelBurrySignal,
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


def _default_signal() -> MichaelBurrySignal:
    return MichaelBurrySignal(signal="neutral", confidence=50, reasoning="Insufficient data for analysis")


def _neutral_result(ticker: str) -> dict[str, Any]:
    return {
        "agent_id": "michael_burry_agent",
        "agent_name": "Michael Burry",
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
        "return_on_equity", "debt_to_equity", "free_cash_flow_yield",
        "net_margin", "operating_margin", "current_ratio",
        "price_to_earnings_ratio", "price_to_book_ratio",
        "enterprise_value_to_ebitda", "revenue_growth",
        "earnings_growth", "market_cap",
    ]
    summary = {k: latest.get(k) for k in keys if latest.get(k) is not None}
    return json.dumps(summary, separators=(",", ":"))