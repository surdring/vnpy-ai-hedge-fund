"""Integration tests for order flow."""
import pytest
from unittest.mock import MagicMock, patch

from vnpy_ai.order_adapter import OrderAdapter
from vnpy_ai.models import PortfolioDecision


class TestOrderFlow:
    """Test end-to-end order flow."""

    def test_buy_decision_sends_order(self):
        """A buy decision should result in an order being sent."""
        mock_engine = MagicMock()
        mock_engine.send_order.return_value = ["test_order_001"]
        mock_engine.get_contract.return_value = None

        adapter = OrderAdapter(mock_engine, gateway_name="CTP")

        decision = PortfolioDecision(
            ticker="AAPL",
            action="buy",
            quantity=100,
            confidence=85,
            reasoning="Strong buy signal",
        )

        result = adapter.send_decision(decision)

        assert result == "test_order_001"
        assert mock_engine.send_order.called

    def test_hold_decision_does_not_send_order(self):
        """A hold decision should not send any order."""
        mock_engine = MagicMock()
        adapter = OrderAdapter(mock_engine)

        decision = PortfolioDecision(
            ticker="AAPL",
            action="hold",
            quantity=0,
            confidence=50,
        )

        result = adapter.send_decision(decision)

        assert result == ""
        assert not mock_engine.send_order.called

    def test_empty_order_list_returns_empty_string(self):
        """When send_order returns empty list, should return empty string."""
        mock_engine = MagicMock()
        mock_engine.send_order.return_value = []
        mock_engine.get_contract.return_value = None

        adapter = OrderAdapter(mock_engine, gateway_name="CTP")

        decision = PortfolioDecision(
            ticker="AAPL",
            action="buy",
            quantity=100,
            confidence=85,
        )

        result = adapter.send_decision(decision)

        assert result == ""

    def test_send_decision_returns_string_not_list(self):
        """send_decision should return a string, not a list or str(list)."""
        mock_engine = MagicMock()
        mock_engine.send_order.return_value = ["CTP.1-1"]
        mock_engine.get_contract.return_value = None

        adapter = OrderAdapter(mock_engine, gateway_name="CTP")

        decision = PortfolioDecision(
            ticker="AAPL",
            action="buy",
            quantity=100,
            confidence=85,
        )

        result = adapter.send_decision(decision)

        # Should be a plain string, not "['CTP.1-1']"
        assert isinstance(result, str)
        assert result == "CTP.1-1"
        assert result != "['CTP.1-1']"