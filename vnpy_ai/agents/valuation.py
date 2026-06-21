"""
Valuation Analyst Agent — DCF, owner earnings, EV/EBITDA, residual income model.

Original upstream: ai-hedge-fund/src/agents/valuation.py
Copyright (c) Virat Singh, MIT License.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from vnpy_ai.utils.llm import call_llm

from .base import AgentBase


class ValuationAnalystSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: int = Field(ge=0, le=100, description="Confidence 0-100")
    reasoning: str = Field(description="Detailed reasoning")


class ValuationAnalystAgent(AgentBase):
    """Valuation Analyst: DCF, owner earnings, EV/EBITDA, residual income, WACC, scenario analysis."""

    agent_id = "valuation_analyst_agent"
    agent_name = "Valuation Analyst"

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
                    "You are a Valuation Analyst specializing in determining intrinsic value "
                    "using multiple complementary methodologies. Analyze the stock's valuation:\n\n"
                    "1. P/E Ratio: Compare to historical average and industry peers.\n"
                    "2. P/B Ratio: Assess relative to book value and ROE.\n"
                    "3. P/S Ratio: Evaluate relative to revenue growth.\n"
                    "4. EV/EBITDA: Enterprise value relative to operating earnings.\n"
                    "5. FCF Yield: Free cash flow as percentage of market cap.\n"
                    "6. PEG Ratio: P/E relative to earnings growth rate.\n\n"
                    "Signal rules:\n"
                    "- Bullish: Undervalued across multiple metrics with margin of safety\n"
                    "- Bearish: Overvalued across multiple metrics\n"
                    "- Neutral: Fairly valued or mixed signals across valuation methods\n\n"
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
            pydantic_model=ValuationAnalystSignal,
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


def _default_signal() -> ValuationAnalystSignal:
    return ValuationAnalystSignal(signal="neutral", confidence=50, reasoning="Insufficient data for analysis")


def _neutral_result(ticker: str) -> dict[str, Any]:
    return {
        "agent_id": "valuation_analyst_agent",
        "agent_name": "Valuation Analyst",
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
        "return_on_equity", "price_to_earnings_ratio", "price_to_book_ratio",
        "price_to_sales_ratio", "enterprise_value_to_ebitda",
        "free_cash_flow_yield", "earnings_growth", "revenue_growth",
        "debt_to_equity", "net_margin", "operating_margin",
        "dividend_yield", "earnings_per_share", "book_value_per_share",
        "market_cap",
    ]
    summary = {k: latest.get(k) for k in keys if latest.get(k) is not None}
    return json.dumps(summary, separators=(",", ":"))