"""Backtest service - runs backtesting simulations via vnpy_ai engine."""

from __future__ import annotations

from typing import Any


class BacktestService:
    """Service for running backtests via :class:`BacktestEngine`.

    Imports of the backtesting engine are deferred to method calls so the
    web backend stays loadable when optional data dependencies are absent.
    """

    def run_backtest(
        self,
        config: Any,
        tickers: list[str],
        strategy: Any = None,
    ) -> dict[str, Any]:
        """Run a backtest and return the result dictionary.

        Args:
            config: A :class:`BacktestConfig` instance or a dict with keys
                ``initial_capital``, ``start_date``, ``end_date``,
                ``commission_rate``, ``slippage``. ``None`` uses defaults.
            tickers: List of ticker symbols to backtest.
            strategy: A callable ``strategy(date, day_data, portfolio)``
                returning a list of decision dicts. ``None`` computes only
                the equity curve from price changes.
        """
        from vnpy_ai.backtesting.engine import BacktestConfig, BacktestEngine

        if config is None:
            bt_config = BacktestConfig()
        elif isinstance(config, BacktestConfig):
            bt_config = config
        elif isinstance(config, dict):
            bt_config = BacktestConfig(
                initial_capital=config.get("initial_capital", 100000.0),
                start_date=config.get("start_date", "2024-01-01"),
                end_date=config.get("end_date", "2024-12-31"),
                commission_rate=config.get("commission_rate", 0.0003),
                slippage=config.get("slippage", 0.001),
            )
        else:
            bt_config = BacktestConfig()

        engine = BacktestEngine(config=bt_config)
        return engine.run(strategy, tickers)
