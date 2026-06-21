"""
Charlie Munger Agent — moat strength, management quality, predictability, mental models.

Original upstream: ai-hedge-fund/src/agents/charlie_munger.py
Copyright (c) Virat Singh, MIT License.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from vnpy_ai.utils.llm import call_llm

from .base import AgentBase


class CharlieMungerSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: int = Field(ge=0, le=100, description="Confidence 0-100")
    reasoning: str = Field(description="Detailed reasoning")


class CharlieMungerAgent(AgentBase):
    """Charlie Munger: moat strength, management quality, business predictability, sensible valuation."""

    agent_id = "charlie_munger_agent"
    agent_name = "Charlie Munger"

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
                    "You are Charlie Munger, Warren Buffett's long-time partner at Berkshire Hathaway. "
                    "Analyze the stock using your mental models and principles:\n"
                    "1. Invest in wonderful businesses at fair prices, not fair businesses at wonderful prices.\n"
                    "2. Focus on durable competitive advantage (moat) - the single most important factor.\n"
                    "3. Management quality is critical: look for integrity, competence, and shareholder orientation.\n"
                    "4. Business predictability: can you see where the company will be in 10 years?\n"
                    "5. Avoid complexity: if it's too hard to understand, move on (too hard pile).\n"
                    "6. Invert, always invert: what could go wrong?\n"
                    "7. Sensible valuation: don't overpay, but quality matters more than price.\n\n"
                    "Signal rules:\n"
                    "- Bullish: Wonderful business, strong moat, great management, fair price\n"
                    "- Bearish: Poor business quality, weak moat, or terrible management\n"
                    "- Neutral: Good business but overpriced, or mixed signals\n\n"
                    "Keep reasoning concise and Munger-like. Return JSON only."
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
            pydantic_model=CharlieMungerSignal,
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


def _default_signal() -> CharlieMungerSignal:
    return CharlieMungerSignal(signal="neutral", confidence=50, reasoning="Insufficient data for analysis")


def _neutral_result(ticker: str) -> dict[str, Any]:
    return {
        "agent_id": "charlie_munger_agent",
        "agent_name": "Charlie Munger",
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
        "free_cash_flow_yield", "price_to_earnings_ratio",
        "price_to_book_ratio", "current_ratio", "market_cap",
    ]
    summary = {k: latest.get(k) for k in keys if latest.get(k) is not None}
    return json.dumps(summary, separators=(",", ":"))