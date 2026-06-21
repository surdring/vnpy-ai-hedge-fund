import logging
from datetime import datetime

from vnpy.trader.constant import Exchange, Interval

logger = logging.getLogger(__name__)


class VnpyAdapter:
    """Bridge between vnpy backtesting framework and AI backtest engine."""

    def __init__(self, main_engine=None):
        self.main_engine = main_engine

    def load_bars(
        self,
        ticker: str,
        start: str,
        end: str,
        interval: Interval = Interval.DAILY,
    ) -> list:
        """Load historical bar data from vnpy database.

        Args:
            ticker: vnpy ticker format "symbol.exchange" (e.g., "AAPL.SMART")
            start: Start date string "YYYY-MM-DD"
            end: End date string "YYYY-MM-DD"
            interval: Bar interval (default: Interval.DAILY)

        Returns:
            List of BarData objects, or empty list if unavailable.
        """
        if self.main_engine is None:
            return []

        try:
            # Parse ticker
            parts = ticker.split(".")
            symbol = parts[0]
            exchange = Exchange(parts[1]) if len(parts) > 1 else Exchange.SMART

            # Parse dates
            start_dt = datetime.strptime(start, "%Y-%m-%d")
            end_dt = datetime.strptime(end, "%Y-%m-%d")

            # Load from database
            database = self.main_engine.database
            if database is None:
                return []

            bars = database.load_bar_data(
                symbol=symbol,
                exchange=exchange,
                interval=interval,
                start=start_dt,
                end=end_dt,
            )
            return bars if bars else []
        except Exception as e:
            logger.warning(f"Failed to load bars for {ticker}: {e}")
            return []

    def convert_to_ai_format(self, bars: list) -> list[dict]:
        return [
            {
                "date": str(b.datetime),
                "open": b.open_price,
                "high": b.high_price,
                "low": b.low_price,
                "close": b.close_price,
                "volume": b.volume,
            }
            for b in bars
        ]
