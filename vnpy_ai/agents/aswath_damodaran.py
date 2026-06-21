"""
Aswath Damodaran Agent — intrinsic value, FCFF DCF, CAPM, relative valuation.

Original upstream: ai-hedge-fund/src/agents/aswath_damodaran.py
Copyright (c) Virat Singh, MIT License.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from vnpy_ai.utils.llm import call_llm

from .base import AgentBase


class AswathDamodaranSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: int = Field(ge=0, le=100, description="Confidence 0-100")
    reasoning: str = Field(description="Detailed reasoning")


class AswathDamodaranAgent(AgentBase):
    """Aswath Damodaran: FCFF DCF, cost of equity, growth & reinvestment, relative valuation."""

    agent_id = "aswath_damodaran_agent"
    agent_name = "Aswath Damodaran"

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
                    "You are Aswath Damodaran, Professor of Finance at NYU Stern. "
                    "Use your valuation framework to issue trading signals on equities.\n\n"
                    "Speak with your usual clear, data-driven tone:\n"
                    "- Start with the company 'story' (qualitatively)\n"
                    "- Connect that story to key numerical drivers: revenue growth, margins, reinvestment, risk\n"
                    "- Conclude with value: your FCFF DCF estimate, margin of safety, and relative valuation sanity checks\n"
                    "- Highlight major uncertainties and how they affect value\n\n"
                    "Key metrics to consider:\n"
                    "- Revenue growth & sustainability\n"
                    "- Operating margins & reinvestment efficiency\n"
                    "- Cost of capital & risk profile\n"
                    "- Free cash flow generation\n"
                    "- Relative valuation vs peers\n\n"
                    "Signal rules:\n"
                    "- Bullish: Significant margin of safety, good growth story, reasonable risk\n"
                    "- Bearish: Overvalued, poor growth prospects, high risk\n"
                    "- Neutral: Fairly valued or uncertain outlook\n\n"
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
            pydantic_model=AswathDamodaranSignal,
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


def _default_signal() -> AswathDamodaranSignal:
    return AswathDamodaranSignal(signal="neutral", confidence=50, reasoning="Insufficient data for analysis")


def _neutral_result(ticker: str) -> dict[str, Any]:
    return {
        "agent_id": "aswath_damodaran_agent",
        "agent_name": "Aswath Damodaran",
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
        "price_to_book_ratio", "enterprise_value_to_ebitda",
        "current_ratio", "market_cap",
    ]
    summary = {k: latest.get(k) for k in keys if latest.get(k) is not None}
    return json.dumps(summary, separators=(",", ":"))