"""Tests for EventAdapter."""
import pytest
from unittest.mock import MagicMock

from vnpy_ai.event_adapter import EventAdapter
from vnpy_ai.models import AnalystSignal, PortfolioDecision


class TestEventAdapter:
    """Test EventAdapter event publishing."""

    def test_publish_signal_event(self):
        """Test that EVENT_AI_SIGNAL events are published correctly."""
        mock_engine = MagicMock()
        adapter = EventAdapter(mock_engine)

        signal = AnalystSignal(
            agent_name="warren_buffett",
            ticker="AAPL",
            signal="buy",
            confidence=85,
            reasoning="Undervalued",
        )
        adapter.publish_signal(signal)

        assert mock_engine.put.called
        event = mock_engine.put.call_args[0][0]
        assert event.type.endswith("AiSignal")

    def test_publish_decision_event(self):
        """Test that EVENT_AI_DECISION events are published."""
        mock_engine = MagicMock()
        adapter = EventAdapter(mock_engine)

        decision = PortfolioDecision(
            ticker="AAPL",
            action="buy",
            confidence=90,
            reasoning="Strong buy signal",
        )
        adapter.publish_decision(decision)

        assert mock_engine.put.called

    def test_publish_error_event(self):
        """Test that EVENT_AI_ERROR events are published."""
        mock_engine = MagicMock()
        adapter = EventAdapter(mock_engine)

        adapter.publish_error(
            message="LLM timeout",
            agent="warren_buffett",
        )

        assert mock_engine.put.called
        # Two events: EVENT_AI_ERROR and EVENT_LOG
        assert mock_engine.put.call_count >= 1
        ai_error_event = mock_engine.put.call_args_list[0][0][0]
        assert ai_error_event.type.endswith("AiError")

    def test_publish_status_event(self):
        """Test that EVENT_AI_STATUS events are published."""
        mock_engine = MagicMock()
        adapter = EventAdapter(mock_engine)

        adapter.publish_status(
            status="running",
            agent="portfolio_manager",
            progress=50.0,
        )

        assert mock_engine.put.called
        event = mock_engine.put.call_args[0][0]
        assert event.type.endswith("AiStatus")