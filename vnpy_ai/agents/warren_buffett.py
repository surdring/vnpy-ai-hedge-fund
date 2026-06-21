"""
Warren Buffett Agent — value investing with moat and owner-earnings focus.

Original upstream: ai-hedge-fund/src/agents/warren_buffett.py
Copyright (c) Virat Singh, MIT License.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from vnpy_ai.utils.llm import call_llm

from .base import AgentBase


class WarrenBuffettSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: int = Field(ge=0, le=100, description="Confidence 0-100")
    reasoning: str = Field(description="Detailed reasoning")


class WarrenBuffettAgent(AgentBase):
    """Warren Buffett: long-term value, durable moat, owner earnings, margin of safety."""

    agent_id = "warren_buffett_agent"
    agent_name = "Warren Buffett"

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
                    "You are Warren Buffett, the Oracle of Omaha. Analyze the stock using your value investing principles.\n"
                    "Checklist:\n"
                    "- Circle of competence: Is this a business you understand?\n"
                    "- Competitive moat: Does the company have a durable competitive advantage?\n"
                    "- Management quality: Is management competent and shareholder-oriented?\n"
                    "- Financial strength: Strong ROE, low debt, consistent earnings\n"
                    "- Owner earnings: True earnings power after maintenance capex\n"
                    "- Margin of safety: Is the stock trading below intrinsic value?\n"
                    "- Long-term prospects: Can the business compound value for decades?\n\n"
                    "Signal rules:\n"
                    "- Bullish: Strong business with durable moat AND margin of safety > 0\n"
                    "- Bearish: Poor business quality OR clearly overvalued\n"
                    "- Neutral: Good business but insufficient margin of safety, or mixed evidence\n\n"
                    "Confidence scale:\n"
                    "- 90-100: Exceptional business within circle of competence, trading at attractive price\n"
                    "- 70-89: Good business with decent moat, fair valuation\n"
                    "- 50-69: Mixed signals, would need more information or better price\n"
                    "- 30-49: Outside expertise or concerning fundamentals\n"
                    "- 10-29: Poor business or significantly overvalued\n\n"
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

            # Build compact data summaries
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
            pydantic_model=WarrenBuffettSignal,
            agent_name=self.agent_id,
            state=state,
            default_factory=_default_warren_buffett_signal,
        )
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "ticker": ticker,
            "signal": result.signal,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
        }


def _default_warren_buffett_signal() -> WarrenBuffettSignal:
    return WarrenBuffettSignal(signal="neutral", confidence=50, reasoning="Insufficient data for analysis")


def _neutral_result(ticker: str) -> dict[str, Any]:
    return {
        "agent_id": "warren_buffett_agent",
        "agent_name": "Warren Buffett",
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
        "current_ratio", "net_margin", "revenue_growth",
        "earnings_growth", "free_cash_flow_yield", "price_to_earnings_ratio",
        "price_to_book_ratio", "market_cap",
    ]
    summary = {k: latest.get(k) for k in keys if latest.get(k) is not None}
    return json.dumps(summary, separators=(",", ":"))