"""
Bill Ackman Agent — activist investing, concentrated bets, catalyst-driven.

Original upstream: ai-hedge-fund/src/agents/bill_ackman.py
Copyright (c) Virat Singh, MIT License.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from vnpy_ai.utils.llm import call_llm

from .base import AgentBase


class BillAckmanSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: int = Field(ge=0, le=100, description="Confidence 0-100")
    reasoning: str = Field(description="Detailed reasoning")


class BillAckmanAgent(AgentBase):
    """Bill Ackman: activist, concentrated, catalyst-driven value investing."""

    agent_id = "bill_ackman_agent"
    agent_name = "Bill Ackman"

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
                    "You are Bill Ackman, a prominent activist investor. Analyze the stock using your principles:\n"
                    "1. Seek high-quality businesses with durable competitive advantages (moats).\n"
                    "2. Prioritize consistent free cash flow and long-term growth potential.\n"
                    "3. Advocate for strong financial discipline (reasonable leverage, efficient capital allocation).\n"
                    "4. Valuation matters: target intrinsic value with a margin of safety.\n"
                    "5. Consider activism where management or operational improvements can unlock substantial upside.\n"
                    "6. Concentrate on a few high-conviction investments.\n\n"
                    "In your reasoning:\n"
                    "- Emphasize brand strength, moat, or unique market positioning.\n"
                    "- Review free cash flow generation and margin trends.\n"
                    "- Analyze leverage, share buybacks, and dividends as capital discipline metrics.\n"
                    "- Provide a valuation assessment with numerical backup.\n"
                    "- Identify any catalysts for activism or value creation.\n"
                    "- Use a confident, analytic, and sometimes confrontational tone.\n\n"
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
            pydantic_model=BillAckmanSignal,
            agent_name=self.agent_id,
            state=state,
            default_factory=_default_ackman_signal,
        )
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "ticker": ticker,
            "signal": result.signal,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
        }


def _default_ackman_signal() -> BillAckmanSignal:
    return BillAckmanSignal(signal="neutral", confidence=50, reasoning="Insufficient data for analysis")


def _neutral_result(ticker: str) -> dict[str, Any]:
    return {
        "agent_id": "bill_ackman_agent",
        "agent_name": "Bill Ackman",
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
        "free_cash_flow_yield", "net_margin", "revenue_growth",
        "earnings_growth", "price_to_earnings_ratio",
        "price_to_book_ratio", "market_cap",
    ]
    summary = {k: latest.get(k) for k in keys if latest.get(k) is not None}
    return json.dumps(summary, separators=(",", ":"))