"""
Sentiment Analyst Agent — insider trading sentiment, news sentiment, combined signals.

Original upstream: ai-hedge-fund/src/agents/sentiment.py
Copyright (c) Virat Singh, MIT License.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from vnpy_ai.utils.llm import call_llm

from .base import AgentBase


class SentimentAnalystSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: int = Field(ge=0, le=100, description="Confidence 0-100")
    reasoning: str = Field(description="Detailed reasoning")


class SentimentAnalystAgent(AgentBase):
    """Sentiment Analyst: insider trading patterns, news sentiment, weighted signal combination."""

    agent_id = "sentiment_analyst_agent"
    agent_name = "Sentiment Analyst"

    def analyze(self, state: dict[str, Any]) -> dict[str, Any]:
        ticker = state.get("ticker", "")
        start_date = state.get("start_date", "")
        end_date = state.get("end_date", "")

        try:
            prices = self.get_prices(ticker, start_date, end_date)
            news = self.get_company_news(ticker)

            template = ChatPromptTemplate.from_messages([
                (
                    "system",
                    "You are a Market Sentiment Analyst specializing in gauging market sentiment "
                    "through insider trading activity, news flow, and social mood indicators.\n\n"
                    "Analysis framework:\n"
                    "1. Insider Trading: Analyze insider buying/selling patterns.\n"
                    "2. News Sentiment: Evaluate overall news tone and sentiment.\n"
                    "3. Fear & Greed: Assess market psychology and sentiment extremes.\n"
                    "4. Contrarian Signal: Extreme sentiment often signals reversals.\n"
                    "5. Weighted Combination: Combine signals with appropriate weights.\n\n"
                    "Signal rules:\n"
                    "- Bullish: Strong insider buying, positive news sentiment, fear extremes (contrarian buy)\n"
                    "- Bearish: Heavy insider selling, negative news, greed extremes (contrarian sell)\n"
                    "- Neutral: Mixed signals, no clear sentiment extreme\n\n"
                    "Return JSON only."
                ),
                (
                    "human",
                    "Ticker: {ticker}\n"
                    "Price data (last {n_prices} points):\n{prices_summary}\n\n"
                    "Recent news ({n_news} items):\n{news_summary}\n\n"
                    "Return exactly:\n"
                    '{{"signal": "bullish" | "bearish" | "neutral", "confidence": int, "reasoning": "short justification"}}'
                ),
            ])

            prices_summary = _summarize_prices(prices)
            news_summary = _summarize_news(news)

            prompt = template.invoke({
                "ticker": ticker,
                "n_prices": len(prices),
                "prices_summary": prices_summary,
                "n_news": len(news),
                "news_summary": news_summary,
            })
        except Exception:
            return _neutral_result(ticker)

        result = call_llm(
            prompt=prompt,
            pydantic_model=SentimentAnalystSignal,
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


def _default_signal() -> SentimentAnalystSignal:
    return SentimentAnalystSignal(signal="neutral", confidence=50, reasoning="Insufficient data for analysis")


def _neutral_result(ticker: str) -> dict[str, Any]:
    return {
        "agent_id": "sentiment_analyst_agent",
        "agent_name": "Sentiment Analyst",
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


def _summarize_news(news: list[dict[str, Any]]) -> str:
    if not news:
        return "No news available"
    summaries = []
    for n in news[:20]:
        title = n.get("title", n.get("headline", ""))
        sentiment = n.get("sentiment", "unknown")
        date = n.get("date", n.get("published_date", ""))
        summaries.append({"title": title, "sentiment": sentiment, "date": date})
    return json.dumps(summaries, separators=(",", ":"))