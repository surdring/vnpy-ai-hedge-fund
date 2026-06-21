"""Unified backtest engine entry point."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

logger = logging.getLogger(__name__)

# Supported backtest modes:
#   - "ai":     AI Hedge Fund backtest via VnpyAdapter + BacktestController (default)
#   - "vnpy":   Delegate to vnpy's native BacktestingEngine (alpha strategy)
#   - "merged": Run AI backtest and merge vnpy daily results when available
BacktestMode = Literal["ai", "vnpy", "merged"]


@dataclass
class BacktestConfig:
    """Backtest configuration parameters."""

    initial_capital: float = 100000.0
    start_date: str = "2024-01-01"
    end_date: str = "2024-12-31"
    commission_rate: float = 0.0003
    slippage: float = 0.001
    # Unified entry mode selector (see BacktestMode).
    mode: BacktestMode = "ai"


@dataclass
class BacktestResult:
    """Container for backtest results."""

    status: str = "complete"
    metrics: dict[str, float] = field(default_factory=dict)
    trades: list[dict[str, Any]] = field(default_factory=list)
    equity_curve: list[dict[str, Any]] = field(default_factory=list)
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "status": self.status,
            "metrics": self.metrics,
            "trades": self.trades,
            "equity_curve": self.equity_curve,
            "message": self.message,
        }


class BacktestEngine:
    """Unified backtest engine that integrates vnpy data loading with AI strategy execution.

    The engine loads historical bar data via :class:`VnpyAdapter`, simulates
    trading through :class:`BacktestController` and :class:`Portfolio`, and
    computes performance metrics via :class:`PerformanceMetrics`.
    """

    def __init__(
        self,
        config: BacktestConfig | None = None,
        main_engine: Any = None,
    ) -> None:
        self.config = config or BacktestConfig()
        self.main_engine = main_engine

    def run(
        self,
        strategy: Any,
        tickers: list[str],
    ) -> dict[str, Any]:
        """Run a backtest with the given strategy and tickers.

        Dispatches to :meth:`_run_ai_mode` or :meth:`_run_vnpy_mode` based on
        ``self.config.mode``. For ``"merged"`` mode, runs the AI backtest and
        attempts to attach vnpy daily results when available; on any vnpy-side
        failure the AI result is returned unchanged with a warning.

        Args:
            strategy: A callable ``strategy(date, day_data, portfolio)`` that
                returns a list of decision dicts. Each decision should contain
                ``ticker``, ``action`` (``buy``/``sell``), ``quantity``.
                If ``None``, no trades are executed and only the equity
                curve from price changes is computed.
            tickers: List of ticker symbols to backtest.

        Returns:
            Dict with keys: ``status``, ``metrics``, ``trades``,
            ``equity_curve``, ``message``.
        """
        mode = self.config.mode
        if mode == "vnpy":
            return self._run_vnpy_mode(strategy, tickers)
        if mode == "merged":
            ai_result = self._run_ai_mode(strategy, tickers)
            if ai_result.get("status") != "complete":
                return ai_result
            try:
                vnpy_result = self._run_vnpy_mode(strategy, tickers)
                if vnpy_result.get("status") == "complete":
                    ai_result["metrics"]["vnpy_final_equity"] = vnpy_result[
                        "metrics"
                    ].get("final_equity", 0.0)
                    ai_result["message"] = "merged: ai+vnpy"
                else:
                    ai_result["message"] = (
                        f"merged: ai only (vnpy failed: "
                        f"{vnpy_result.get('message', 'unknown')})"
                    )
            except Exception as e:
                logger.warning("vnpy mode failed during merged run: %s", e)
                ai_result["message"] = f"merged: ai only (vnpy failed: {e})"
            return ai_result
        # default: ai
        return self._run_ai_mode(strategy, tickers)

    def _run_ai_mode(
        self,
        strategy: Any,
        tickers: list[str],
    ) -> dict[str, Any]:
        """AI Hedge Fund backtest via VnpyAdapter + BacktestController."""
        try:
            # --- Load historical data via VnpyAdapter ---
            from vnpy_ai.backtesting.vnpy_adapter import VnpyAdapter

            adapter = VnpyAdapter(self.main_engine)

            all_bars: dict[str, list[dict[str, Any]]] = {}
            for ticker in tickers:
                bars = adapter.load_bars(
                    ticker,
                    self.config.start_date,
                    self.config.end_date,
                )
                if bars:
                    all_bars[ticker] = adapter.convert_to_ai_format(bars)

            if not all_bars:
                logger.warning(
                    "No bars loaded for any ticker; backtest cannot proceed"
                )
                return BacktestResult(
                    status="error",
                    message="No data loaded for the given tickers and date range",
                ).to_dict()

            # --- Initialize simulation components ---
            from vnpy_ai.backtesting.controller import BacktestController
            from vnpy_ai.backtesting.portfolio import Portfolio

            portfolio = Portfolio(initial_capital=self.config.initial_capital)
            controller = BacktestController(
                initial_capital=self.config.initial_capital,
                commission_rate=self.config.commission_rate,
                slippage=self.config.slippage,
            )

            trades: list[dict[str, Any]] = []
            equity_curve: list[dict[str, Any]] = []

            # --- Collect and sort all trading dates ---
            all_dates: set[str] = set()
            for bars in all_bars.values():
                all_dates.update(b["date"] for b in bars)
            sorted_dates = sorted(all_dates)

            # --- Iterate through each trading day ---
            for date in sorted_dates:
                # Build day's market data: {ticker: bar_dict}
                day_data: dict[str, dict[str, Any]] = {}
                for ticker, bars in all_bars.items():
                    day_bars = [b for b in bars if b["date"] == date]
                    if day_bars:
                        day_data[ticker] = day_bars[0]

                if not day_data:
                    continue

                # --- Get strategy decisions ---
                decisions: list[dict[str, Any]] = []
                if strategy is not None:
                    try:
                        decisions = strategy(date, day_data, portfolio) or []
                    except Exception as e:
                        logger.warning(
                            "Strategy execution failed on %s: %s", date, e
                        )
                        decisions = []

                # --- Execute decisions ---
                for decision in decisions:
                    ticker = decision.get("ticker", "")
                    action = decision.get("action", "hold")
                    quantity = int(decision.get("quantity", 0))

                    if action == "hold" or quantity <= 0 or ticker not in day_data:
                        continue

                    price = float(day_data[ticker].get("close", 0))
                    if price <= 0:
                        continue

                    is_buy = action == "buy"
                    exec_price = controller.apply_slippage(price, is_buy=is_buy)

                    # Update portfolio
                    portfolio.update(ticker, quantity, exec_price, is_buy=is_buy)

                    # Apply commission
                    commission = exec_price * quantity * controller.commission_rate
                    portfolio.cash -= commission

                    # Record trade
                    trade = {
                        "date": date,
                        "ticker": ticker,
                        "action": action,
                        "quantity": quantity,
                        "price": exec_price,
                        "commission": commission,
                        "cash_after": portfolio.cash,
                    }
                    trades.append(trade)

                # --- Update portfolio equity for the day ---
                prices_map = {
                    ticker: float(bar.get("close", 0))
                    for ticker, bar in day_data.items()
                }
                total_equity = portfolio.get_total_equity(prices_map)
                portfolio.equity_history.append(total_equity)

                equity_curve.append(
                    {
                        "date": date,
                        "equity": total_equity,
                        "cash": portfolio.cash,
                    }
                )

            # --- Calculate performance metrics ---
            from vnpy_ai.backtesting.metrics import PerformanceMetrics

            equity_values = [point["equity"] for point in equity_curve]
            # Daily returns from equity curve
            returns: list[float] = []
            for i in range(1, len(equity_values)):
                prev = equity_values[i - 1]
                if prev > 0:
                    returns.append((equity_values[i] - prev) / prev)
                else:
                    returns.append(0.0)

            days = len(equity_values)
            metrics = {
                "sharpe_ratio": PerformanceMetrics.sharpe_ratio(returns),
                "sortino_ratio": PerformanceMetrics.sortino_ratio(returns),
                "max_drawdown": PerformanceMetrics.max_drawdown(equity_values),
                "annualized_return": PerformanceMetrics.annualized_return(
                    equity_values, days=max(days, 1)
                ),
                "win_rate": PerformanceMetrics.win_rate(trades),
                "total_trades": float(len(trades)),
                "final_equity": float(equity_values[-1]) if equity_values else 0.0,
                "initial_capital": float(self.config.initial_capital),
                "total_return": (
                    float(
                        (equity_values[-1] / self.config.initial_capital - 1)
                        * 100
                    )
                    if equity_values and self.config.initial_capital > 0
                    else 0.0
                ),
            }

            return BacktestResult(
                status="complete",
                metrics=metrics,
                trades=trades,
                equity_curve=equity_curve,
            ).to_dict()

        except Exception as e:
            logger.error("Backtest failed: %s", e, exc_info=True)
            return BacktestResult(
                status="error",
                message=str(e),
            ).to_dict()

    def _run_vnpy_mode(
        self,
        strategy: Any,
        tickers: list[str],
    ) -> dict[str, Any]:
        """Delegate to vnpy's native alpha BacktestingEngine when available.

        The vnpy alpha engine requires an ``AlphaLab`` instance and a configured
        ``AlphaStrategy``. When those are not available (e.g. unit tests or
        standalone usage), this method returns an ``error`` result with a clear
        message, allowing callers to fall back to AI mode.
        """
        try:
            from vnpy.alpha.strategy.backtesting import BacktestingEngine as VnpyBtEngine
        except ImportError:
            return BacktestResult(
                status="error",
                message="vnpy alpha BacktestingEngine not available",
            ).to_dict()

        try:
            # The vnpy alpha engine is constructed with an AlphaLab instance.
            # When callers pass a pre-configured engine via main_engine, use it;
            # otherwise we cannot construct a lab here without configuration.
            lab = getattr(self.main_engine, "alpha_lab", None) if self.main_engine else None
            if lab is None:
                return BacktestResult(
                    status="error",
                    message="vnpy mode requires main_engine with alpha_lab attribute",
                ).to_dict()

            engine = VnpyBtEngine(lab)
            # The caller is responsible for set_parameters + add_strategy on the
            # vnpy engine via the strategy object; here we only invoke the
            # native run_backtesting if the strategy exposes it.
            if hasattr(strategy, "run_backtesting"):
                strategy.run_backtesting(engine)
            else:
                engine.run_backtesting()

            # Extract daily results if available
            daily_results = getattr(engine, "daily_results", {})
            equity_curve: list[dict[str, Any]] = []
            equity_values: list[float] = []
            for dt in sorted(daily_results.keys()):
                result = daily_results[dt]
                total_equity = float(getattr(result, "total_pnl", 0)) + float(
                    getattr(engine, "capital", self.config.initial_capital)
                )
                equity_values.append(total_equity)
                equity_curve.append(
                    {"date": str(dt), "equity": total_equity}
                )

            from vnpy_ai.backtesting.metrics import PerformanceMetrics

            returns: list[float] = []
            for i in range(1, len(equity_values)):
                prev = equity_values[i - 1]
                if prev > 0:
                    returns.append((equity_values[i] - prev) / prev)
                else:
                    returns.append(0.0)

            metrics = {
                "sharpe_ratio": PerformanceMetrics.sharpe_ratio(returns),
                "sortino_ratio": PerformanceMetrics.sortino_ratio(returns),
                "max_drawdown": PerformanceMetrics.max_drawdown(equity_values),
                "annualized_return": PerformanceMetrics.annualized_return(
                    equity_values, days=max(len(equity_values), 1)
                ),
                "final_equity": float(equity_values[-1]) if equity_values else 0.0,
                "initial_capital": float(self.config.initial_capital),
                "total_return": (
                    float(
                        (equity_values[-1] / self.config.initial_capital - 1) * 100
                    )
                    if equity_values and self.config.initial_capital > 0
                    else 0.0
                ),
            }

            return BacktestResult(
                status="complete",
                metrics=metrics,
                trades=[],
                equity_curve=equity_curve,
                message="vnpy native backtest",
            ).to_dict()
        except Exception as e:
            logger.error("vnpy backtest failed: %s", e, exc_info=True)
            return BacktestResult(
                status="error",
                message=str(e),
            ).to_dict()
