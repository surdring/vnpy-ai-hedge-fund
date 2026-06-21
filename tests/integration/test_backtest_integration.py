"""Integration tests for the unified backtest engine.

These tests exercise the BacktestEngine dispatch logic (ai / vnpy / merged
modes), the VnpyAdapter bridge, and the performance metrics computation. They
use mock data and a mock main_engine so they run without a live vnpy database.
"""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from vnpy_ai.backtesting.engine import BacktestConfig, BacktestEngine, BacktestResult
from vnpy_ai.backtesting.vnpy_adapter import VnpyAdapter


def _make_bar(date_str: str, close: float, open_: float | None = None,
              high: float | None = None, low: float | None = None,
              volume: int = 1_000_000):
    """Build a lightweight BarData-like object for tests."""
    return SimpleNamespace(
        datetime=datetime.strptime(date_str, "%Y-%m-%d"),
        open_price=float(open_ if open_ is not None else close),
        high_price=float(high if high is not None else close * 1.01),
        low_price=float(low if low is not None else close * 0.99),
        close_price=float(close),
        volume=volume,
    )


@pytest.fixture
def mock_main_engine_with_bars():
    """A mock main_engine whose database returns 5 days of AAPL bars."""
    bars = [
        _make_bar("2024-01-02", 185.00),
        _make_bar("2024-01-03", 186.50),
        _make_bar("2024-01-04", 188.20),
        _make_bar("2024-01-05", 190.10),
        _make_bar("2024-01-08", 192.30),
    ]
    database = MagicMock()
    database.load_bar_data.return_value = bars
    engine = MagicMock()
    engine.database = database
    return engine


class TestVnpyAdapter:
    """Tests for the VnpyAdapter data bridge."""

    def test_load_bars_returns_empty_without_main_engine(self):
        adapter = VnpyAdapter(main_engine=None)
        bars = adapter.load_bars("AAPL.SMART", "2024-01-01", "2024-01-31")
        assert bars == []

    def test_load_bars_returns_bars_from_database(self, mock_main_engine_with_bars):
        adapter = VnpyAdapter(main_engine=mock_main_engine_with_bars)
        bars = adapter.load_bars("AAPL.SMART", "2024-01-01", "2024-01-31")
        assert len(bars) == 5
        assert bars[0].close_price == 185.00

    def test_convert_to_ai_format(self, mock_main_engine_with_bars):
        adapter = VnpyAdapter(main_engine=mock_main_engine_with_bars)
        bars = adapter.load_bars("AAPL.SMART", "2024-01-01", "2024-01-31")
        converted = adapter.convert_to_ai_format(bars)
        assert len(converted) == 5
        assert converted[0]["close"] == 185.00
        assert "date" in converted[0]
        assert "volume" in converted[0]

    def test_load_bars_handles_database_exception(self):
        engine = MagicMock()
        engine.database.load_bar_data.side_effect = RuntimeError("db error")
        adapter = VnpyAdapter(main_engine=engine)
        bars = adapter.load_bars("AAPL.SMART", "2024-01-01", "2024-01-31")
        assert bars == []


class TestBacktestEngineAiMode:
    """Tests for the default AI backtest mode."""

    def test_run_returns_error_when_no_data(self):
        """Without a main_engine, no bars can be loaded -> error result."""
        config = BacktestConfig(
            start_date="2024-01-01", end_date="2024-01-31", mode="ai"
        )
        engine = BacktestEngine(config=config, main_engine=None)
        result = engine.run(strategy=None, tickers=["AAPL.SMART"])
        assert result["status"] == "error"
        assert "No data loaded" in result["message"]

    def test_run_computes_equity_curve_with_no_trades(self, mock_main_engine_with_bars):
        """With no strategy, only the equity curve from price changes is computed."""
        config = BacktestConfig(
            initial_capital=100000.0,
            start_date="2024-01-01",
            end_date="2024-01-31",
            mode="ai",
        )
        engine = BacktestEngine(config=config, main_engine=mock_main_engine_with_bars)
        result = engine.run(strategy=None, tickers=["AAPL.SMART"])

        assert result["status"] == "complete"
        assert len(result["equity_curve"]) == 5
        assert result["metrics"]["total_trades"] == 0.0
        assert result["metrics"]["initial_capital"] == 100000.0
        # final_equity should equal initial_capital since no trades were made
        assert result["metrics"]["final_equity"] == pytest.approx(100000.0)

    def test_run_executes_buy_strategy(self, mock_main_engine_with_bars):
        """A simple buy-on-first-day strategy should produce one trade."""

        def buy_strategy(date, day_data, portfolio):
            if date == "2024-01-02 00:00:00":
                return [
                    {
                        "ticker": "AAPL.SMART",
                        "action": "buy",
                        "quantity": 100,
                    }
                ]
            return []

        config = BacktestConfig(
            initial_capital=100000.0,
            start_date="2024-01-01",
            end_date="2024-01-31",
            mode="ai",
        )
        engine = BacktestEngine(config=config, main_engine=mock_main_engine_with_bars)
        result = engine.run(strategy=buy_strategy, tickers=["AAPL.SMART"])

        assert result["status"] == "complete"
        assert result["metrics"]["total_trades"] == 1.0
        assert len(result["trades"]) == 1
        assert result["trades"][0]["action"] == "buy"
        assert result["trades"][0]["quantity"] == 100

    def test_run_metrics_contain_sharpe_and_drawdown(self, mock_main_engine_with_bars):
        config = BacktestConfig(
            start_date="2024-01-01", end_date="2024-01-31", mode="ai"
        )
        engine = BacktestEngine(config=config, main_engine=mock_main_engine_with_bars)
        result = engine.run(strategy=None, tickers=["AAPL.SMART"])

        metrics = result["metrics"]
        assert "sharpe_ratio" in metrics
        assert "sortino_ratio" in metrics
        assert "max_drawdown" in metrics
        assert "annualized_return" in metrics
        assert "total_return" in metrics


class TestBacktestEngineVnpyMode:
    """Tests for the vnpy native backtest mode dispatch."""

    def test_vnpy_mode_returns_error_without_alpha_lab(self):
        """Without main_engine.alpha_lab, vnpy mode should return a clear error."""
        config = BacktestConfig(mode="vnpy")
        engine = BacktestEngine(config=config, main_engine=None)
        result = engine.run(strategy=None, tickers=["AAPL.SMART"])
        assert result["status"] == "error"
        assert "alpha_lab" in result["message"] or "not available" in result["message"]


class TestBacktestEngineMergedMode:
    """Tests for the merged mode that combines AI + vnpy results."""

    def test_merged_mode_returns_ai_result_when_vnpy_fails(self, mock_main_engine_with_bars):
        """When vnpy mode fails, merged mode should still return the AI result."""
        config = BacktestConfig(
            start_date="2024-01-01",
            end_date="2024-01-31",
            mode="merged",
        )
        engine = BacktestEngine(config=config, main_engine=mock_main_engine_with_bars)
        result = engine.run(strategy=None, tickers=["AAPL.SMART"])

        # AI mode should succeed; vnpy mode should fail (no alpha_lab).
        assert result["status"] == "complete"
        assert "merged" in result.get("message", "")


class TestBacktestResultDataclass:
    """Tests for the BacktestResult dataclass."""

    def test_to_dict_contains_all_fields(self):
        result = BacktestResult(
            status="complete",
            metrics={"sharpe_ratio": 1.5},
            trades=[{"ticker": "AAPL"}],
            equity_curve=[{"date": "2024-01-01", "equity": 100000}],
            message="ok",
        )
        d = result.to_dict()
        assert d["status"] == "complete"
        assert d["metrics"]["sharpe_ratio"] == 1.5
        assert len(d["trades"]) == 1
        assert d["message"] == "ok"
