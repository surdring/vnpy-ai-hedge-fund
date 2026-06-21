"""
Nassim Taleb Agent — antifragility, tail risk, convexity, skin in the game.

Original upstream: ai-hedge-fund/src/agents/nassim_taleb.py
Copyright (c) Virat Singh, MIT License.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from vnpy_ai.utils.llm import call_llm

from .base import AgentBase


class NassimTalebSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: int = Field(ge=0, le=100, description="Confidence 0-100")
    reasoning: str = Field(description="Detailed reasoning")


class NassimTalebAgent(AgentBase):
    """Nassim Taleb: antifragility, tail risk, convexity, fragility detection, volatility regime."""

    agent_id = "nassim_taleb_agent"
    agent_name = "Nassim Taleb"

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
                    "You are Nassim Taleb, author of 'The Black Swan' and 'Antifragile'. "
                    "Analyze the stock using your framework:\n\n"
                    "Checklist for decision:\n"
                    "- Antifragility (benefits from disorder)\n"
                    "- Tail risk profile (fat tails, skewness)\n"
                    "- Convexity (asymmetric payoff potential)\n"
                    "- Fragility via negativa (avoid the fragile)\n"
                    "- Skin in the game (insider alignment)\n"
                    "- Volatility regime (low vol = danger)\n\n"
                    "Signal rules:\n"
                    "- Bullish: Antifragile business with convex payoff AND not fragile\n"
                    "- Bearish: Fragile business (high leverage, thin margins, volatile earnings) OR no skin in the game\n"
                    "- Neutral: Mixed signals, or insufficient data to judge fragility\n\n"
                    "Confidence scale:\n"
                    "- 90-100: Truly antifragile with strong convexity and skin in the game\n"
                    "- 70-89: Low fragility with decent optionality\n"
                    "- 50-69: Mixed fragility signals, uncertain tail exposure\n"
                    "- 30-49: Some fragility detected, weak insider alignment\n"
                    "- 10-29: Clearly fragile or dangerous vol regime\n\n"
                    "Use Taleb's vocabulary: antifragile, convexity, skin in the game, via negativa, barbell, turkey problem, Lindy effect.\n"
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
            pydantic_model=NassimTalebSignal,
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


def _default_signal() -> NassimTalebSignal:
    return NassimTalebSignal(signal="neutral", confidence=50, reasoning="Insufficient data for analysis")


def _neutral_result(ticker: str) -> dict[str, Any]:
    return {
        "agent_id": "nassim_taleb_agent",
        "agent_name": "Nassim Taleb",
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
        "net_margin", "free_cash_flow_yield", "current_ratio",
        "price_to_earnings_ratio", "price_to_book_ratio",
        "revenue_growth", "earnings_growth", "market_cap",
    ]
    summary = {k: latest.get(k) for k in keys if latest.get(k) is not None}
    return json.dumps(summary, separators=(",", ":"))