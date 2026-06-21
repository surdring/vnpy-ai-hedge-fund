"""
Cathie Wood Agent — disruptive innovation, high-growth, long-duration.

Original upstream: ai-hedge-fund/src/agents/cathie_wood.py
Copyright (c) Virat Singh, MIT License.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from vnpy_ai.utils.llm import call_llm

from .base import AgentBase


class CathieWoodSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: int = Field(ge=0, le=100, description="Confidence 0-100")
    reasoning: str = Field(description="Detailed reasoning")


class CathieWoodAgent(AgentBase):
    """Cathie Wood: disruptive innovation, exponential growth, long time horizon."""

    agent_id = "cathie_wood_agent"
    agent_name = "Cathie Wood"

    def analyze(self, state: dict[str, Any]) -> dict[str, Any]:
        ticker = state.get("ticker", "")
        start_date = state.get("start_date", "")
        end_date = state.get("end_date", "")

        try:
            prices = self.get_prices(ticker, start_date, end_date)
            metrics = self.get_financial_metrics(ticker)
            news = self.get_company_news(ticker)

            template = ChatPromptTemplate.from_messages([
                (
                    "system",
                    "You are Cathie Wood, CEO of ARK Invest. Analyze the stock using your principles:\n"
                    "1. Seek companies leveraging disruptive innovation.\n"
                    "2. Emphasize exponential growth potential and large TAM (Total Addressable Market).\n"
                    "3. Focus on technology, genomics, fintech, AI, robotics, blockchain, and other future-facing sectors.\n"
                    "4. Consider multi-year time horizons for potential breakthroughs.\n"
                    "5. Accept higher volatility in pursuit of high returns.\n"
                    "6. Evaluate management's vision and ability to invest in R&D.\n\n"
                    "Rules:\n"
                    "- Identify disruptive or breakthrough technology.\n"
                    "- Evaluate strong potential for multi-year revenue growth.\n"
                    "- Check if the company can scale effectively in a large market.\n"
                    "- Use a growth-biased valuation approach.\n\n"
                    "Signal rules:\n"
                    "- Bullish: Clear disruptive innovation with exponential growth trajectory\n"
                    "- Bearish: Lacking true innovation, slowing growth, or incremental improvements only\n"
                    "- Neutral: Promising technology but early-stage or uncertain execution\n\n"
                    "Return JSON only."
                ),
                (
                    "human",
                    "Ticker: {ticker}\n"
                    "Price data (last {n_prices} points):\n{prices_summary}\n\n"
                    "Financial metrics (latest):\n{metrics_summary}\n\n"
                    "Recent news (last {n_news} items):\n{news_summary}\n\n"
                    "Return exactly:\n"
                    '{{"signal": "bullish" | "bearish" | "neutral", "confidence": int, "reasoning": "short justification"}}'
                ),
            ])

            prices_summary = _summarize_prices(prices)
            metrics_summary = _summarize_metrics(metrics)
            news_summary = _summarize_news(news)

            prompt = template.invoke({
                "ticker": ticker,
                "n_prices": len(prices),
                "prices_summary": prices_summary,
                "metrics_summary": metrics_summary,
                "n_news": len(news),
                "news_summary": news_summary,
            })
        except Exception:
            return _neutral_result(ticker)

        result = call_llm(
            prompt=prompt,
            pydantic_model=CathieWoodSignal,
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


def _default_signal() -> CathieWoodSignal:
    return CathieWoodSignal(signal="neutral", confidence=50, reasoning="Insufficient data for analysis")


def _neutral_result(ticker: str) -> dict[str, Any]:
    return {
        "agent_id": "cathie_wood_agent",
        "agent_name": "Cathie Wood",
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
        "return_on_equity", "revenue_growth", "earnings_growth",
        "operating_margin", "net_margin", "debt_to_equity",
        "free_cash_flow_yield", "price_to_earnings_ratio",
        "market_cap",
    ]
    summary = {k: latest.get(k) for k in keys if latest.get(k) is not None}
    return json.dumps(summary, separators=(",", ":"))


def _summarize_news(news: list[dict[str, Any]]) -> str:
    if not news:
        return "No news available"
    titles = [n.get("title", n.get("headline", "")) for n in news[:10]]
    return json.dumps(titles, separators=(",", ":"))