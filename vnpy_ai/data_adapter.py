"""
Data adapter from VeighNa data objects to AI Hedge Fund compatible models.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any, cast

from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import AccountData, BarData, PositionData, TickData

from .data.cache import Cache
from .models import InsiderTrade, Price

logger = logging.getLogger(__name__)


def parse_vt_symbol(vt_symbol: str, default_exchange: Exchange = Exchange.SMART) -> tuple[str, Exchange]:
    """Parse `symbol.EXCHANGE` into VeighNa symbol and exchange."""

    if "." not in vt_symbol:
        return vt_symbol, default_exchange
    symbol, exchange_value = vt_symbol.rsplit(".", 1)
    try:
        return symbol, Exchange(exchange_value)
    except ValueError:
        return symbol, default_exchange


def bar_to_price(bar: BarData) -> Price:
    """Convert a VeighNa bar into an AI Hedge Fund price."""

    return Price(
        open=float(bar.open_price),
        close=float(bar.close_price),
        high=float(bar.high_price),
        low=float(bar.low_price),
        volume=int(bar.volume or 0),
        time=bar.datetime.date().isoformat(),
    )


def tick_to_price(tick: TickData) -> Price:
    """Convert a VeighNa tick into a single price snapshot."""

    price = float(tick.last_price or tick.pre_close or 0)
    return Price(
        open=float(tick.open_price or price),
        close=price,
        high=float(tick.high_price or price),
        low=float(tick.low_price or price),
        volume=int(tick.volume or 0),
        time=tick.datetime.isoformat(),
    )


class DataAdapter:
    """Read VeighNa data and expose AI Hedge Fund compatible data APIs."""

    def __init__(self, main_engine: Any | None = None, datafeed: Any | None = None) -> None:
        self.main_engine = main_engine
        self._datafeed = datafeed
        self._cache = Cache(default_ttl=300)

    # ---------- datafeed extension (TASK #10) ----------

    def set_datafeed(self, datafeed: Any) -> None:
        """Set an external datafeed for financial metrics and news queries."""
        self._datafeed = datafeed

    # ---------- cache (TASK #12) ----------

    def clear_cache(self) -> None:
        """Clear all cached data entries."""
        self._cache.clear()

    # ---------- price data ----------

    def get_prices(self, ticker: str, start_date: str, end_date: str) -> list[Price]:
        """Load daily OHLCV prices from the VeighNa database with caching."""

        cache_key = f"prices:{ticker}:{start_date}:{end_date}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cast(list[Price], cached)

        from vnpy.trader.database import get_database

        symbol, exchange = parse_vt_symbol(ticker)

        # --- date validation (TASK #11) ---
        try:
            start = datetime.fromisoformat(start_date)
        except (ValueError, TypeError):
            logger.warning("Invalid start_date '%s', falling back to 1 year ago", start_date)
            start = datetime.combine(date.today() - timedelta(days=365), datetime.min.time())

        try:
            end = datetime.fromisoformat(end_date)
        except (ValueError, TypeError):
            logger.warning("Invalid end_date '%s', falling back to today", end_date)
            end = datetime.combine(date.today(), datetime.max.time())

        bars = get_database().load_bar_data(symbol, exchange, Interval.DAILY, start, end)
        result = [bar_to_price(bar) for bar in bars]
        self._cache.set(cache_key, result)
        return result

    def get_latest_price(self, ticker: str) -> Price | None:
        """Return the latest in-memory tick as a price snapshot."""

        if not self.main_engine or not hasattr(self.main_engine, "get_tick"):
            return None
        tick = self.main_engine.get_tick(ticker)
        if not tick:
            return None
        return tick_to_price(tick)

    # ---------- portfolio (TASK #9) ----------

    def get_portfolio(self, tickers: list[str] | None = None) -> dict[str, Any]:
        """Return portfolio with positions, account info, and total equity."""

        accounts: list[AccountData] = []
        positions: list[PositionData] = []

        if self.main_engine:
            if hasattr(self.main_engine, "get_all_accounts"):
                accounts = list(self.main_engine.get_all_accounts())
            if hasattr(self.main_engine, "get_all_positions"):
                positions = list(self.main_engine.get_all_positions())

        # Build positions list
        wanted = set(tickers or [])
        positions_list: list[dict[str, Any]] = []
        for pos in positions:
            vt_symbol = pos.vt_symbol
            if wanted and vt_symbol not in wanted and pos.symbol not in wanted:
                continue
            positions_list.append({
                "ticker": vt_symbol,
                "quantity": float(pos.volume),
                "avg_cost": float(pos.price),
                "current_price": 0.0,
                "market_value": 0.0,
            })

        # Fill zero positions for requested tickers with no actual position
        covered = {p["ticker"] for p in positions_list}
        for t in wanted:
            if t not in covered:
                positions_list.append({
                    "ticker": t,
                    "quantity": 0,
                    "avg_cost": 0.0,
                    "current_price": 0.0,
                    "market_value": 0.0,
                })

        # Build account info
        account_info: dict[str, float] = {
            "balance": 0.0,
            "available": 0.0,
            "frozen": 0.0,
            "margin": 0.0,
        }
        if accounts:
            account_info["balance"] = sum(float(a.balance) for a in accounts)
            account_info["available"] = sum(float(a.available) for a in accounts)
            account_info["frozen"] = sum(float(a.frozen) for a in accounts)
            account_info["margin"] = sum(float(a.margin) for a in accounts)

        total_equity = account_info["balance"] + sum(
            p.get("market_value", 0.0) for p in positions_list
        )

        return {
            "positions": positions_list,
            "account": account_info,
            "total_equity": total_equity,
            "cash": account_info["available"],
        }

    # ---------- financial metrics (TASK #7) ----------

    def get_financial_metrics(self, ticker: str) -> list[dict[str, Any]]:
        """Return financial metrics from datafeed, with caching."""

        cache_key = f"metrics:{ticker}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cast(list[dict[str, Any]], cached)

        if self._datafeed is None:
            return []

        try:
            result = cast(list[dict[str, Any]], self._datafeed.query_financial_metrics(ticker))
            self._cache.set(cache_key, result)
            return result
        except Exception:
            logger.debug("Failed to get financial metrics from datafeed", exc_info=True)
            return []

    # ---------- company news (TASK #8) ----------

    def get_company_news(self, ticker: str) -> list[dict[str, Any]]:
        """Return company news from datafeed."""

        if self._datafeed is None:
            return []

        try:
            return cast(list[dict[str, Any]], self._datafeed.query_company_news(ticker))
        except Exception:
            logger.debug("Failed to get company news from datafeed", exc_info=True)
            return []

    # ---------- insider trades (unchanged) ----------

    def get_insider_trades(self, ticker: str, end_date: str, start_date: str | None = None, limit: int = 1000) -> list[InsiderTrade]:
        """Return insider trades when a future datafeed implementation provides them."""

        return []
