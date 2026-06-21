"""Mock market data fixtures for integration tests.

Provides reusable Price/Bar dictionaries and DataAdapter stubs so that
integration tests can run without a live vnpy database or datafeed.
"""

from __future__ import annotations

from typing import Any

from vnpy_ai.models import Price


def make_price(date: str, close: float, open_: float | None = None,
               high: float | None = None, low: float | None = None,
               volume: int = 1_000_000) -> Price:
    """Build a Price object with sensible defaults."""
    return Price(
        open=float(open_ if open_ is not None else close),
        close=float(close),
        high=float(high if high is not None else close * 1.01),
        low=float(low if low is not None else close * 0.99),
        volume=volume,
        time=date,
    )


# 5-day ascending price series for AAPL
MOCK_AAPL_PRICES: list[Price] = [
    make_price("2024-01-02", 185.00),
    make_price("2024-01-03", 186.50),
    make_price("2024-01-04", 188.20),
    make_price("2024-01-05", 190.10),
    make_price("2024-01-08", 192.30),
]

# 5-day descending price series for GOOGL
MOCK_GOOGLE_PRICES: list[Price] = [
    make_price("2024-01-02", 140.00),
    make_price("2024-01-03", 138.50),
    make_price("2024-01-04", 137.20),
    make_price("2024-01-05", 135.80),
    make_price("2024-01-08", 134.50),
]

# Combined price dict keyed by ticker (AI Hedge Fund format)
MOCK_PRICES_BY_TICKER: dict[str, list[Price]] = {
    "AAPL": MOCK_AAPL_PRICES,
    "GOOGL": MOCK_GOOGLE_PRICES,
}

# Financial metrics in the dict-list format expected by agents
MOCK_FINANCIAL_METRICS: dict[str, list[dict[str, Any]]] = {
    "AAPL": [
        {
            "ticker": "AAPL",
            "report_period": "2024-Q1",
            "period": "ttm",
            "currency": "USD",
            "market_cap": 2_800_000_000_000,
            "price_to_earnings_ratio": 28.5,
            "price_to_book_ratio": 45.2,
            "return_on_equity": 0.45,
            "debt_to_equity": 1.8,
            "free_cash_flow": 100_000_000_000,
        }
    ],
    "GOOGL": [
        {
            "ticker": "GOOGL",
            "report_period": "2024-Q1",
            "period": "ttm",
            "currency": "USD",
            "market_cap": 1_800_000_000_000,
            "price_to_earnings_ratio": 25.1,
            "price_to_book_ratio": 6.2,
            "return_on_equity": 0.27,
            "debt_to_equity": 0.1,
            "free_cash_flow": 70_000_000_000,
        }
    ],
}

# Company news mock
MOCK_COMPANY_NEWS: dict[str, list[dict[str, Any]]] = {
    "AAPL": [
        {
            "ticker": "AAPL",
            "title": "Apple announces new product line",
            "source": "Reuters",
            "date": "2024-01-03",
            "url": "https://example.com/aapl-news",
            "sentiment": "positive",
        }
    ],
    "GOOGL": [
        {
            "ticker": "GOOGL",
            "title": "Google faces antitrust ruling",
            "source": "Bloomberg",
            "date": "2024-01-04",
            "url": "https://example.com/googl-news",
            "sentiment": "negative",
        }
    ],
}

# Mock portfolio state
MOCK_PORTFOLIO: dict[str, Any] = {
    "positions": [
        {
            "ticker": "AAPL",
            "quantity": 100,
            "avg_cost": 180.0,
            "current_price": 192.30,
            "market_value": 19230.0,
        }
    ],
    "account": {
        "balance": 100000.0,
        "available": 80770.0,
        "frozen": 0.0,
        "margin": 0.0,
    },
    "total_equity": 119230.0,
    "cash": 80770.0,
}


class MockDataAdapter:
    """In-memory DataAdapter stub backed by the mock data above.

    Implements the subset of :class:`vnpy_ai.data_adapter.DataAdapter` methods
    used by :class:`AgentBase` and the workflow runner.
    """

    def __init__(
        self,
        prices: dict[str, list[Price]] | None = None,
        metrics: dict[str, list[dict[str, Any]]] | None = None,
        news: dict[str, list[dict[str, Any]]] | None = None,
        portfolio: dict[str, Any] | None = None,
    ) -> None:
        self._prices = prices if prices is not None else MOCK_PRICES_BY_TICKER
        self._metrics = metrics if metrics is not None else MOCK_FINANCIAL_METRICS
        self._news = news if news is not None else MOCK_COMPANY_NEWS
        self._portfolio = portfolio if portfolio is not None else MOCK_PORTFOLIO

    def get_prices(self, ticker: str, start_date: str, end_date: str) -> list[Price]:
        return list(self._prices.get(ticker, []))

    def get_financial_metrics(self, ticker: str) -> list[dict[str, Any]]:
        return list(self._metrics.get(ticker, []))

    def get_company_news(self, ticker: str) -> list[dict[str, Any]]:
        return list(self._news.get(ticker, []))

    def get_portfolio(self, tickers: list[str] | None = None) -> dict[str, Any]:
        return dict(self._portfolio)

    def get_latest_price(self, ticker: str) -> Price | None:
        prices = self._prices.get(ticker)
        return prices[-1] if prices else None
