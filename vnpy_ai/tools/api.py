"""
Data fetching API for the VeighNa AI Hedge Fund integration.

Adapted from ai-hedge-fund/src/tools/api.py (MIT License, Virat Singh).
All data access is delegated to a `DataAdapter` instance injected via
`set_data_adapter()` instead of calling the Financial Datasets API directly.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import pandas as pd

from vnpy_ai.models import FinancialMetrics, Price

if TYPE_CHECKING:
    from vnpy_ai.data_adapter import DataAdapter

logger = logging.getLogger(__name__)

# Module-level DataAdapter instance injected by the host application.
_data_adapter: DataAdapter | None = None


def set_data_adapter(adapter: DataAdapter | None) -> None:
    """Inject the DataAdapter instance used by all data fetching functions.

    Args:
        adapter: DataAdapter instance, or None to clear.
    """
    global _data_adapter
    _data_adapter = adapter


def _require_adapter() -> DataAdapter:
    """Return the injected DataAdapter or raise a RuntimeError."""
    if _data_adapter is None:
        raise RuntimeError(
            "DataAdapter not configured. Call set_data_adapter() before using tools.api."
        )
    return _data_adapter


def get_prices(
    ticker: str,
    start_date: str,
    end_date: str,
    api_key: str | None = None,
) -> list[Price]:
    """Fetch daily OHLCV prices for a ticker via the DataAdapter.

    Args:
        ticker: Ticker symbol (may include exchange suffix like `AAPL.SMART`).
        start_date: ISO date string (YYYY-MM-DD).
        end_date: ISO date string (YYYY-MM-DD).
        api_key: Ignored; kept for upstream signature compatibility.

    Returns:
        List of Price objects; empty list on failure.
    """
    adapter = _require_adapter()
    try:
        return adapter.get_prices(ticker, start_date, end_date)
    except Exception:
        logger.warning("Failed to fetch prices for %s", ticker, exc_info=True)
        return []


def get_financial_metrics(
    ticker: str,
    end_date: str = "",
    period: str = "ttm",
    limit: int = 10,
    api_key: str | None = None,
) -> list[FinancialMetrics]:
    """Fetch financial metrics for a ticker via the DataAdapter.

    The DataAdapter currently exposes only `get_financial_metrics(ticker)`;
    `end_date`, `period`, `limit` are accepted for upstream compatibility but
    may be ignored by the underlying datafeed.

    Args:
        ticker: Ticker symbol.
        end_date: ISO date string (optional, ignored by default adapter).
        period: Reporting period (ignored by default adapter).
        limit: Maximum number of records (ignored by default adapter).
        api_key: Ignored; kept for upstream signature compatibility.

    Returns:
        List of FinancialMetrics objects; empty list on failure.
    """
    adapter = _require_adapter()
    try:
        raw_metrics = adapter.get_financial_metrics(ticker)
    except Exception:
        logger.warning("Failed to fetch financial metrics for %s", ticker, exc_info=True)
        return []

    results: list[FinancialMetrics] = []
    for raw in raw_metrics:
        if isinstance(raw, FinancialMetrics):
            results.append(raw)
            continue
        if not isinstance(raw, dict):
            continue
        try:
            results.append(
                FinancialMetrics(
                    ticker=raw.get("ticker", ticker),
                    report_period=raw.get("report_period", end_date or ""),
                    period=raw.get("period", period),
                    currency=raw.get("currency", "USD"),
                    market_cap=raw.get("market_cap"),
                    price_to_earnings_ratio=raw.get("price_to_earnings_ratio"),
                    price_to_book_ratio=raw.get("price_to_book_ratio"),
                    return_on_equity=raw.get("return_on_equity"),
                )
            )
        except Exception:
            logger.debug("Skipping malformed metric entry for %s: %s", ticker, raw)
            continue
    return results[:limit] if limit > 0 else results


def search_line_items(
    ticker: str,
    line_items: list[str],
    end_date: str = "",
    period: str = "ttm",
    limit: int = 10,
    api_key: str | None = None,
) -> list[dict[str, Any]]:
    """Search financial line items for a ticker.

    The default DataAdapter does not expose line-item search; this function
    returns an empty list unless the injected adapter implements
    `search_line_items()`.

    Args:
        ticker: Ticker symbol.
        line_items: List of line-item names to retrieve.
        end_date: ISO date string (optional).
        period: Reporting period.
        limit: Maximum number of records.
        api_key: Ignored; kept for upstream signature compatibility.

    Returns:
        List of line-item dicts; empty list if unavailable.
    """
    adapter = _require_adapter()
    method = getattr(adapter, "search_line_items", None)
    if method is None:
        logger.debug(
            "DataAdapter does not implement search_line_items; returning empty list"
        )
        return []
    try:
        result = method(ticker, line_items, end_date, period, limit)
        return list(result or [])[:limit]
    except Exception:
        logger.warning(
            "Failed to search line items for %s", ticker, exc_info=True
        )
        return []


def get_market_cap(
    ticker: str,
    end_date: str = "",
    api_key: str | None = None,
) -> float | None:
    """Fetch the market cap for a ticker.

    Falls back to the latest financial metrics' `market_cap` field when the
    DataAdapter does not expose a dedicated `get_market_cap()` method.

    Args:
        ticker: Ticker symbol.
        end_date: ISO date string (optional).
        api_key: Ignored; kept for upstream signature compatibility.

    Returns:
        Market cap as float, or None if unavailable.
    """
    adapter = _require_adapter()

    # Prefer a dedicated adapter method when available.
    dedicated = getattr(adapter, "get_market_cap", None)
    if dedicated is not None:
        try:
            value = dedicated(ticker, end_date)
            if value is not None:
                return float(value)
        except Exception:
            logger.debug("Dedicated get_market_cap failed for %s", ticker, exc_info=True)

    # Fallback: derive from financial metrics.
    metrics = get_financial_metrics(ticker, end_date=end_date, api_key=api_key)
    if not metrics:
        return None
    market_cap = metrics[0].market_cap
    if market_cap is None:
        return None
    return float(market_cap)


def prices_to_df(prices: list[Price]) -> pd.DataFrame:
    """Convert a list of Price objects into a sorted DataFrame.

    Args:
        prices: List of Price objects.

    Returns:
        DataFrame indexed by Date with numeric OHLCV columns.
    """
    if not prices:
        return pd.DataFrame(
            columns=["open", "close", "high", "low", "volume", "time"]
        )

    df = pd.DataFrame([p.model_dump() for p in prices])
    df["Date"] = pd.to_datetime(df["time"])
    df.set_index("Date", inplace=True)
    numeric_cols = ["open", "close", "high", "low", "volume"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.sort_index(inplace=True)
    return df


def get_price_data(
    ticker: str,
    start_date: str,
    end_date: str,
    api_key: str | None = None,
) -> pd.DataFrame:
    """Convenience wrapper: fetch prices and return as a DataFrame."""
    prices = get_prices(ticker, start_date, end_date, api_key=api_key)
    return prices_to_df(prices)


# Backwards-compatible alias used by some upstream agents.
def get_company_news(
    ticker: str,
    end_date: str = "",
    start_date: str | None = None,
    limit: int = 1000,
    api_key: str | None = None,
) -> list[dict[str, Any]]:
    """Fetch company news for a ticker via the DataAdapter."""
    adapter = _require_adapter()
    try:
        return list(adapter.get_company_news(ticker) or [])
    except Exception:
        logger.warning("Failed to fetch company news for %s", ticker, exc_info=True)
        return []


def get_insider_trades(
    ticker: str,
    end_date: str = "",
    start_date: str | None = None,
    limit: int = 1000,
    api_key: str | None = None,
) -> list[Any]:
    """Fetch insider trades for a ticker via the DataAdapter."""
    adapter = _require_adapter()
    try:
        return list(
            adapter.get_insider_trades(ticker, end_date, start_date, limit) or []
        )
    except Exception:
        logger.warning("Failed to fetch insider trades for %s", ticker, exc_info=True)
        return []
