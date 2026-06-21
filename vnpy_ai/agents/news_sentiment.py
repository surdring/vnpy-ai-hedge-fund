"""
News Sentiment Analyst Agent — news article sentiment classification, LLM-driven analysis.

Original upstream: ai-hedge-fund/src/agents/news_sentiment.py
Copyright (c) Virat Singh, MIT License.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from vnpy_ai.utils.llm import call_llm

from .base import AgentBase


class NewsSentimentAnalystSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: int = Field(ge=0, le=100, description="Confidence 0-100")
    reasoning: str = Field(description="Detailed reasoning")


class NewsSentimentAnalystAgent(AgentBase):
    """News Sentiment Analyst: LLM-driven news sentiment classification, confidence-weighted aggregation."""

    agent_id = "news_sentiment_analyst_agent"
    agent_name = "News Sentiment Analyst"

    def analyze(self, state: dict[str, Any]) -> dict[str, Any]:
        ticker = state.get("ticker", "")
        start_date = state.get("start_date", "")
        end_date = state.get("end_date", "")

        try:
            news = self.get_company_news(ticker)

            template = ChatPromptTemplate.from_messages([
                (
                    "system",
                    "You are a News Sentiment Analyst specializing in extracting market-moving signals "
                    "from financial news articles. Analyze the provided news to determine overall sentiment.\n\n"
                    "Analysis framework:\n"
                    "1. Identify key themes: product launches, earnings reports, regulatory changes, M&A, etc.\n"
                    "2. Classify each article's sentiment: positive, negative, or neutral.\n"
                    "3. Weight by importance: major announcements > minor mentions.\n"
                    "4. Aggregate: determine overall bullish/bearish/neutral signal.\n"
                    "5. Consider source credibility and recency.\n\n"
                    "Signal rules:\n"
                    "- Bullish: Overwhelmingly positive news with strong catalysts\n"
                    "- Bearish: Overwhelmingly negative news with significant risks\n"
                    "- Neutral: Mixed news or insufficient significant news\n\n"
                    "Return JSON only."
                ),
                (
                    "human",
                    "Ticker: {ticker}\n"
                    "Recent news articles ({n_news} items):\n{news_summary}\n\n"
                    "Return exactly:\n"
                    '{{"signal": "bullish" | "bearish" | "neutral", "confidence": int, "reasoning": "short justification"}}'
                ),
            ])

            news_summary = _summarize_news(news)

            prompt = template.invoke({
                "ticker": ticker,
                "n_news": len(news),
                "news_summary": news_summary,
            })
        except Exception:
            return _neutral_result(ticker)

        result = call_llm(
            prompt=prompt,
            pydantic_model=NewsSentimentAnalystSignal,
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


def _default_signal() -> NewsSentimentAnalystSignal:
    return NewsSentimentAnalystSignal(signal="neutral", confidence=50, reasoning="Insufficient data for analysis")


def _neutral_result(ticker: str) -> dict[str, Any]:
    return {
        "agent_id": "news_sentiment_analyst_agent",
        "agent_name": "News Sentiment Analyst",
        "ticker": ticker,
        "signal": "neutral",
        "confidence": 50,
        "reasoning": "Error fetching data, defaulting to neutral",
    }


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