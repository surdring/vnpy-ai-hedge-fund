"""
Fundamentals Analyst Agent — financial ratios, income statement, balance sheet analysis.

Original upstream: ai-hedge-fund/src/agents/fundamentals.py
Copyright (c) Virat Singh, MIT License.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from vnpy_ai.utils.llm import call_llm

from .base import AgentBase


class FundamentalsAnalystSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: int = Field(ge=0, le=100, description="Confidence 0-100")
    reasoning: str = Field(description="Detailed reasoning")


class FundamentalsAnalystAgent(AgentBase):
    """Fundamentals Analyst: financial ratios, income statement, balance sheet, cash flow analysis."""

    agent_id = "fundamentals_analyst_agent"
    agent_name = "Fundamentals Analyst"

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
                    "You are a Fundamentals Analyst specializing in financial statement analysis. "
                    "Analyze the company's financial health using the provided metrics:\n\n"
                    "1. Profitability: ROE, net margin, operating margin, gross margin.\n"
                    "2. Liquidity: Current ratio, quick ratio, cash position.\n"
                    "3. Leverage: Debt-to-equity, interest coverage, debt ratios.\n"
                    "4. Efficiency: Asset turnover, inventory turnover, ROIC.\n"
                    "5. Cash Flow: Free cash flow yield, operating cash flow, FCF conversion.\n"
                    "6. Growth: Revenue growth, earnings growth, book value growth.\n\n"
                    "Signal rules:\n"
                    "- Bullish: Strong profitability, healthy balance sheet, good cash flow, growing\n"
                    "- Bearish: Weak profitability, high leverage, poor cash flow, declining\n"
                    "- Neutral: Mixed fundamentals or mediocre across the board\n\n"
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
            pydantic_model=FundamentalsAnalystSignal,
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


def _default_signal() -> FundamentalsAnalystSignal:
    return FundamentalsAnalystSignal(signal="neutral", confidence=50, reasoning="Insufficient data for analysis")


def _neutral_result(ticker: str) -> dict[str, Any]:
    return {
        "agent_id": "fundamentals_analyst_agent",
        "agent_name": "Fundamentals Analyst",
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
        "operating_margin", "net_margin", "gross_margin",
        "revenue_growth", "earnings_growth", "book_value_growth",
        "free_cash_flow_yield", "price_to_earnings_ratio",
        "price_to_book_ratio", "enterprise_value_to_ebitda",
        "return_on_invested_capital", "asset_turnover",
        "market_cap",
    ]
    summary = {k: latest.get(k) for k in keys if latest.get(k) is not None}
    return json.dumps(summary, separators=(",", ":"))