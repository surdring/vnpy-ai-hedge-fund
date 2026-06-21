"""
Stanley Druckenmiller Agent — asymmetric risk-reward, growth momentum, capital preservation.

Original upstream: ai-hedge-fund/src/agents/stanley_druckenmiller.py
Copyright (c) Virat Singh, MIT License.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from vnpy_ai.utils.llm import call_llm

from .base import AgentBase


class StanleyDruckenmillerSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: int = Field(ge=0, le=100, description="Confidence 0-100")
    reasoning: str = Field(description="Detailed reasoning")


class StanleyDruckenmillerAgent(AgentBase):
    """Stanley Druckenmiller: asymmetric risk-reward, growth momentum, sentiment, capital preservation."""

    agent_id = "stanley_druckenmiller_agent"
    agent_name = "Stanley Druckenmiller"

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
                    "You are Stanley Druckenmiller, one of the greatest macro hedge fund managers. "
                    "Analyze the stock using your principles:\n"
                    "1. Seek asymmetric risk-reward opportunities (large upside, limited downside).\n"
                    "2. Emphasize growth, momentum, and market sentiment.\n"
                    "3. Preserve capital by avoiding major drawdowns.\n"
                    "4. Willing to pay higher valuations for true growth leaders.\n"
                    "5. Be aggressive when conviction is high.\n"
                    "6. Cut losses quickly if the thesis changes.\n\n"
                    "Rules:\n"
                    "- Reward companies showing strong revenue/earnings growth and positive stock momentum.\n"
                    "- Evaluate sentiment as supportive or contradictory signals.\n"
                    "- Watch out for high leverage or extreme volatility that threatens capital.\n\n"
                    "When providing your reasoning:\n"
                    "1. Explain the growth and momentum metrics that most influenced your decision.\n"
                    "2. Highlight the risk-reward profile with specific evidence.\n"
                    "3. Discuss market sentiment and catalysts that could drive price action.\n"
                    "4. Address both upside potential and downside risks.\n"
                    "5. Use Druckenmiller's decisive, momentum-focused, conviction-driven voice.\n\n"
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
            pydantic_model=StanleyDruckenmillerSignal,
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


def _default_signal() -> StanleyDruckenmillerSignal:
    return StanleyDruckenmillerSignal(signal="neutral", confidence=50, reasoning="Insufficient data for analysis")


def _neutral_result(ticker: str) -> dict[str, Any]:
    return {
        "agent_id": "stanley_druckenmiller_agent",
        "agent_name": "Stanley Druckenmiller",
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