"""
Technical Analyst Agent — price trends, momentum, volume, chart patterns.

Original upstream: ai-hedge-fund/src/agents/technicals.py
Copyright (c) Virat Singh, MIT License.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from vnpy_ai.utils.llm import call_llm

from .base import AgentBase


class TechnicalAnalystSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: int = Field(ge=0, le=100, description="Confidence 0-100")
    reasoning: str = Field(description="Detailed reasoning")


class TechnicalAnalystAgent(AgentBase):
    """Technical Analyst: price trends, momentum indicators, volume analysis, chart patterns."""

    agent_id = "technical_analyst_agent"
    agent_name = "Technical Analyst"

    def analyze(self, state: dict[str, Any]) -> dict[str, Any]:
        ticker = state.get("ticker", "")
        start_date = state.get("start_date", "")
        end_date = state.get("end_date", "")

        try:
            prices = self.get_prices(ticker, start_date, end_date)

            template = ChatPromptTemplate.from_messages([
                (
                    "system",
                    "You are a Technical Analyst specializing in price action, momentum, "
                    "and market structure analysis. Analyze the price data using technical methods:\n\n"
                    "1. Trend Following: Identify primary trend direction (uptrend, downtrend, sideways).\n"
                    "2. Moving Averages: Check SMA crossovers, price relative to key MAs.\n"
                    "3. Momentum: Analyze RSI, MACD, stochastic oscillators.\n"
                    "4. Support/Resistance: Identify key price levels.\n"
                    "5. Volume Analysis: Confirm price moves with volume.\n"
                    "6. Volatility: Assess Bollinger Bands, ATR, volatility regime.\n\n"
                    "Signal rules:\n"
                    "- Bullish: Strong uptrend with confirming momentum and volume\n"
                    "- Bearish: Clear downtrend with bearish momentum divergence\n"
                    "- Neutral: Sideways/choppy market, mixed signals, or low conviction\n\n"
                    "Return JSON only."
                ),
                (
                    "human",
                    "Ticker: {ticker}\n"
                    "Price data ({n_prices} data points):\n{prices_summary}\n\n"
                    "Return exactly:\n"
                    '{{"signal": "bullish" | "bearish" | "neutral", "confidence": int, "reasoning": "short justification"}}'
                ),
            ])

            prices_summary = _summarize_prices_detailed(prices)

            prompt = template.invoke({
                "ticker": ticker,
                "n_prices": len(prices),
                "prices_summary": prices_summary,
            })
        except Exception:
            return _neutral_result(ticker)

        result = call_llm(
            prompt=prompt,
            pydantic_model=TechnicalAnalystSignal,
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


def _default_signal() -> TechnicalAnalystSignal:
    return TechnicalAnalystSignal(signal="neutral", confidence=50, reasoning="Insufficient data for analysis")


def _neutral_result(ticker: str) -> dict[str, Any]:
    return {
        "agent_id": "technical_analyst_agent",
        "agent_name": "Technical Analyst",
        "ticker": ticker,
        "signal": "neutral",
        "confidence": 50,
        "reasoning": "Error fetching data, defaulting to neutral",
    }


def _summarize_prices_detailed(prices: list[dict[str, Any]]) -> str:
    if not prices:
        return "No price data available"
    # Include more detail for technical analysis: OHLCV for recent periods
    recent = prices[-20:] if len(prices) >= 20 else prices
    summary = [{
        "date": p.get("date", ""),
        "open": p.get("open", "N/A"),
        "high": p.get("high", "N/A"),
        "low": p.get("low", "N/A"),
        "close": p.get("close", "N/A"),
        "volume": p.get("volume", "N/A"),
    } for p in recent]
    return json.dumps(summary, separators=(",", ":"))