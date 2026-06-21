"""Integration tests for the vnpy <-> vnpy_ai bridge.

These tests verify that the vnpy MainEngine can load the AiHedgeFundApp, that
the AiHedgeFundEngine wires up its adapters correctly, and that the new
``add_ai_agent`` semantic alias on MainEngine works as expected.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine

from vnpy_ai.app import AiHedgeFundApp
from vnpy_ai.engine import AiHedgeFundEngine
from vnpy_ai.models import AgentStatus, PortfolioDecision


@pytest.fixture
def main_engine():
    event_engine = EventEngine()
    engine = MainEngine(event_engine)
    yield engine
    engine.close()


class TestMainEngineIntegration:
    """Tests for MainEngine <-> AiHedgeFundApp wiring."""

    def test_add_app_returns_ai_engine(self, main_engine):
        engine = main_engine.add_app(AiHedgeFundApp)
        assert isinstance(engine, AiHedgeFundEngine)

    def test_add_ai_agent_alias_returns_ai_engine(self, main_engine):
        """The add_ai_agent semantic alias should behave like add_app."""
        engine = main_engine.add_ai_agent(AiHedgeFundApp)
        assert isinstance(engine, AiHedgeFundEngine)

    def test_engine_status_disabled_by_default(self, main_engine):
        engine = main_engine.add_app(AiHedgeFundApp)
        status = engine.get_status()
        assert isinstance(status, AgentStatus)
        assert status.enabled is False


class TestEngineWorkflowIntegration:
    """Tests for the AiHedgeFundEngine.run_workflow path with mocked workflow."""

    def test_run_workflow_returns_workflow_result(self, main_engine):
        engine = main_engine.add_app(AiHedgeFundApp)

        # Patch the workflow runner to return a deterministic decision without
        # requiring a live LLM or market data.
        from vnpy_ai.models import WorkflowResult

        fake_result = WorkflowResult(
            decisions={
                "AAPL": PortfolioDecision(
                    ticker="AAPL",
                    action="buy",
                    quantity=10,
                    confidence=80,
                )
            }
        )
        with patch.object(engine.workflow_runner, "run", return_value=fake_result):
            result = engine.run_workflow(["AAPL"])

        assert "AAPL" in result.decisions
        assert result.decisions["AAPL"].action == "buy"

    def test_run_workflow_publishes_events(self, main_engine):
        engine = main_engine.add_app(AiHedgeFundApp)

        from vnpy_ai.models import WorkflowResult

        fake_result = WorkflowResult(
            decisions={
                "AAPL": PortfolioDecision(ticker="AAPL", action="hold")
            }
        )
        with patch.object(engine.workflow_runner, "run", return_value=fake_result):
            with patch.object(engine.event_adapter, "publish_workflow_result") as pub:
                engine.run_workflow(["AAPL"])
                assert pub.called

    def test_run_workflow_fallback_on_exception(self, main_engine):
        engine = main_engine.add_app(AiHedgeFundApp)

        with patch.object(
            engine.workflow_runner, "run", side_effect=RuntimeError("boom")
        ):
            result = engine.run_workflow(["AAPL"])

        # Should return a degraded WorkflowResult, not raise.
        assert result.degraded is True
        assert "AAPL" in result.decisions
        assert result.error == "boom"


class TestEngineAutoTrading:
    """Tests for the auto-trading path in submit_decision."""

    def test_submit_decision_no_auto_trading_publishes_only(self, main_engine):
        engine = main_engine.add_app(AiHedgeFundApp)
        # Default settings have enable_auto_trading=False
        assert engine.settings.enable_auto_trading is False

        decision = PortfolioDecision(ticker="AAPL", action="buy", quantity=10)
        with patch.object(engine.event_adapter, "publish_decision") as pub:
            with patch.object(engine.order_adapter, "send_decision") as send:
                orderid = engine.submit_decision(decision)
                assert pub.called
                assert not send.called
                assert orderid == ""

    def test_submit_decision_auto_trading_sends_order(self, main_engine):
        engine = main_engine.add_app(AiHedgeFundApp)
        engine.settings.enable_auto_trading = True

        decision = PortfolioDecision(ticker="AAPL", action="buy", quantity=10)
        with patch.object(
            engine.order_adapter, "send_decision", return_value="ORD-001"
        ) as send:
            with patch.object(engine.event_adapter, "publish_order_decision") as pub:
                orderid = engine.submit_decision(decision)
                assert send.called
                assert pub.called
                assert orderid == "ORD-001"


class TestEngineMarketEventTrigger:
    """Tests for the on_market_event trigger logic."""

    def test_disabled_engine_ignores_market_event(self, main_engine):
        engine = main_engine.add_app(AiHedgeFundApp)
        engine.settings.enabled = False

        fake_event = MagicMock()
        fake_event.data = MagicMock(vt_symbol="AAPL.SSE")

        with patch.object(engine, "run_workflow") as run:
            engine.on_market_event(fake_event)
            assert not run.called

    def test_enabled_engine_triggers_workflow(self, main_engine):
        engine = main_engine.add_app(AiHedgeFundApp)
        engine.settings.enabled = True
        engine.settings.trigger_frequency = "tick"
        engine.settings.signal_cooldown = 0  # no cooldown for the test

        fake_event = MagicMock()
        fake_event.data = MagicMock(vt_symbol="AAPL.SSE")

        with patch.object(engine, "run_workflow") as run:
            engine.on_market_event(fake_event)
            assert run.called
            args, _ = run.call_args
            assert args[0] == ["AAPL.SSE"]
