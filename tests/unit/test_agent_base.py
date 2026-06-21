"""Tests for AgentBase."""
import pytest
from unittest.mock import MagicMock

from vnpy_ai.agents.base import AgentBase


class TestAgentBase:
    """Test AgentBase data fetching methods."""

    def test_get_prices_delegates_to_adapter(self):
        """get_prices should delegate to DataAdapter."""
        mock_adapter = MagicMock()
        mock_adapter.get_prices.return_value = [{"close": 150.0}]

        agent = AgentBase(mock_adapter)
        result = agent.get_prices("AAPL", "2024-01-01", "2024-06-30")

        mock_adapter.get_prices.assert_called_once_with(
            "AAPL", "2024-01-01", "2024-06-30"
        )
        assert result == [{"close": 150.0}]

    def test_get_financial_metrics_delegates_to_adapter(self):
        """get_financial_metrics should delegate to DataAdapter."""
        mock_adapter = MagicMock()
        mock_adapter.get_financial_metrics.return_value = []

        agent = AgentBase(mock_adapter)
        result = agent.get_financial_metrics("AAPL")

        assert result == []

    def test_get_company_news_delegates_to_adapter(self):
        """get_company_news should delegate to DataAdapter."""
        mock_adapter = MagicMock()
        mock_adapter.get_company_news.return_value = []

        agent = AgentBase(mock_adapter)
        result = agent.get_company_news("AAPL")

        assert result == []

    def test_get_portfolio_delegates_to_adapter(self):
        """get_portfolio should delegate to DataAdapter."""
        mock_adapter = MagicMock()
        mock_adapter.get_portfolio.return_value = {"cash": 100000}

        agent = AgentBase(mock_adapter)
        result = agent.get_portfolio()

        mock_adapter.get_portfolio.assert_called_once()
        assert result == {"cash": 100000}

    def test_analyze_raises_not_implemented(self):
        """analyze() should raise NotImplementedError."""
        mock_adapter = MagicMock()
        agent = AgentBase(mock_adapter)

        with pytest.raises(NotImplementedError):
            agent.analyze({})

    def test_agent_id_and_name_defaults(self):
        """AgentBase should have default agent_id and agent_name."""
        mock_adapter = MagicMock()
        agent = AgentBase(mock_adapter)

        assert agent.agent_id == ""
        assert agent.agent_name == ""