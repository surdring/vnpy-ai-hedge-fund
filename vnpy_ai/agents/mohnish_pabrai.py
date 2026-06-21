"""
Mohnish Pabrai Agent — downside protection, cloning, heads-I-win-tails-I-don't-lose-much.

Original upstream: ai-hedge-fund/src/agents/mohnish_pabrai.py
Copyright (c) Virat Singh, MIT License.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from vnpy_ai.utils.llm import call_llm

from .base import AgentBase


class MohnishPabraiSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: int = Field(ge=0, le=100, description="Confidence 0-100")
    reasoning: str = Field(description="Detailed reasoning")


class MohnishPabraiAgent(AgentBase):
    """Mohnish Pabrai: downside protection, FCF yield, doubling potential, cloning great investors."""

    agent_id = "mohnish_pabrai_agent"
    agent_name = "Mohnish Pabrai"

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
                    "You are Mohnish Pabrai, a value investor who follows the Buffett/Munger philosophy. "
                    "Apply your value investing framework:\n"
                    "- Heads I win; tails I don't lose much: prioritize downside protection first.\n"
                    "- Buy businesses with simple, understandable models and durable moats.\n"
                    "- Demand high free cash flow yields and low leverage; prefer asset-light models.\n"
                    "- Look for situations where intrinsic value is rising and price is significantly lower.\n"
                    "- Favor cloning great investors' ideas and checklists over novelty.\n"
                    "- Seek potential to double capital in 2-3 years with low risk.\n"
                    "- Avoid leverage, complexity, and fragile balance sheets.\n\n"
                    "Provide candid, checklist-driven reasoning, "
                    "with emphasis on capital preservation and expected mispricing.\n\n"
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
            pydantic_model=MohnishPabraiSignal,
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


def _default_signal() -> MohnishPabraiSignal:
    return MohnishPabraiSignal(signal="neutral", confidence=50, reasoning="Insufficient data for analysis")


def _neutral_result(ticker: str) -> dict[str, Any]:
    return {
        "agent_id": "mohnish_pabrai_agent",
        "agent_name": "Mohnish Pabrai",
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
        "net_margin", "operating_margin", "revenue_growth",
        "earnings_growth", "price_to_earnings_ratio",
        "price_to_book_ratio", "current_ratio", "market_cap",
    ]
    summary = {k: latest.get(k) for k in keys if latest.get(k) is not None}
    return json.dumps(summary, separators=(",", ":"))