"""Tests for engine workflow and fallback behavior."""
import pytest
from unittest.mock import MagicMock, patch

from vnpy_ai.workflow.runner import WorkflowRunner, create_initial_state
from vnpy_ai.models import WorkflowResult, PortfolioDecision


class TestWorkflowFallback:
    """Test WorkflowRunner fallback behavior."""

    def test_fallback_returns_hold_all_tickers(self):
        """Fallback should return hold decisions for all tickers."""
        mock_adapter = MagicMock()
        mock_adapter.get_portfolio.return_value = {}
        mock_adapter.get_prices.return_value = []

        runner = WorkflowRunner(mock_adapter)
        result = runner.run(tickers=["AAPL", "GOOGL"])

        assert isinstance(result, WorkflowResult)
        assert len(result.decisions) == 2
        assert result.degraded is True

        for ticker in ["AAPL", "GOOGL"]:
            assert ticker in result.decisions
            assert result.decisions[ticker].action == "hold"
            assert result.decisions[ticker].confidence == 0

    def test_fallback_confidence_is_zero(self):
        """Fallback confidence should always be 0, not 100."""
        mock_adapter = MagicMock()
        mock_adapter.get_portfolio.return_value = {}
        mock_adapter.get_prices.return_value = []

        runner = WorkflowRunner(mock_adapter)
        result = runner.run(tickers=["AAPL"])

        assert result.decisions["AAPL"].confidence == 0

    def test_fallback_degraded_flag(self):
        """Fallback should set degraded=True."""
        mock_adapter = MagicMock()
        mock_adapter.get_portfolio.return_value = {}
        mock_adapter.get_prices.return_value = []

        runner = WorkflowRunner(mock_adapter)
        result = runner.run(tickers=["AAPL"])

        assert result.degraded is True


class TestCreateInitialState:
    """Test create_initial_state function."""

    def test_creates_state_with_tickers(self):
        """Initial state should contain provided tickers."""
        state = create_initial_state(
            tickers=["AAPL", "GOOGL"],
            portfolio={},
        )

        assert "AAPL" in state["data"]["tickers"]
        assert "GOOGL" in state["data"]["tickers"]

    def test_creates_state_with_dates(self):
        """Initial state should contain date range."""
        state = create_initial_state(
            tickers=["AAPL"],
            portfolio={},
            start_date="2024-01-01",
            end_date="2024-06-30",
        )

        assert state["data"]["start_date"] == "2024-01-01"
        assert state["data"]["end_date"] == "2024-06-30"