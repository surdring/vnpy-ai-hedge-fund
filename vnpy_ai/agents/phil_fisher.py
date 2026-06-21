"""
Phil Fisher Agent — growth at a reasonable price, scuttlebutt method.

Original upstream: ai-hedge-fund/src/agents/phil_fisher.py
Copyright (c) Virat Singh, MIT License.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from vnpy_ai.utils.llm import call_llm

from .base import AgentBase


class PhilFisherSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: int = Field(ge=0, le=100, description="Confidence 0-100")
    reasoning: str = Field(description="Detailed reasoning")


class PhilFisherAgent(AgentBase):
    """Phil Fisher: growth investing, scuttlebutt research, quality management."""

    agent_id = "phil_fisher_agent"
    agent_name = "Phil Fisher"

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
                    "You are Phil Fisher, author of 'Common Stocks and Uncommon Profits'. "
                    "Analyze the stock using your scuttlebutt approach:\n"
                    "1. Emphasize long-term growth potential and quality of management.\n"
                    "2. Focus on companies investing in R&D for future products/services.\n"
                    "3. Look for strong profitability and consistent margins.\n"
                    "4. Willing to pay more for exceptional companies but still mindful of valuation.\n"
                    "5. Rely on thorough research (scuttlebutt) and thorough fundamental checks.\n\n"
                    "When providing your reasoning:\n"
                    "1. Discuss the company's growth prospects with specific metrics and trends.\n"
                    "2. Evaluate management quality and their capital allocation decisions.\n"
                    "3. Highlight R&D investments and product pipeline.\n"
                    "4. Assess consistency of margins and profitability.\n"
                    "5. Explain competitive advantages that could sustain growth over 3-5+ years.\n"
                    "6. Use Phil Fisher's methodical, growth-focused, and long-term oriented voice.\n\n"
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
            pydantic_model=PhilFisherSignal,
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


def _default_signal() -> PhilFisherSignal:
    return PhilFisherSignal(signal="neutral", confidence=50, reasoning="Insufficient data for analysis")


def _neutral_result(ticker: str) -> dict[str, Any]:
    return {
        "agent_id": "phil_fisher_agent",
        "agent_name": "Phil Fisher",
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
        "price_to_book_ratio", "market_cap",
    ]
    summary = {k: latest.get(k) for k in keys if latest.get(k) is not None}
    return json.dumps(summary, separators=(",", ":"))


def _summarize_news(news: list[dict[str, Any]]) -> str:
    if not news:
        return "No news available"
    titles = [n.get("title", n.get("headline", "")) for n in news[:10]]
    return json.dumps(titles, separators=(",", ":"))