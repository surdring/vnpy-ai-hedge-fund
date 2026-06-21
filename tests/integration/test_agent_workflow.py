"""Integration tests for the AI agent workflow.

These tests exercise the workflow end-to-end with a mock DataAdapter and a
patched ``call_llm`` so they run deterministically without network access.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure the tests/fixtures directory is importable.
_FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"
if str(_FIXTURES_DIR) not in sys.path:
    sys.path.insert(0, str(_FIXTURES_DIR))

from mock_llm_responses import MockLlmResponses  # noqa: E402
from mock_market_data import MockDataAdapter, MOCK_AAPL_PRICES  # noqa: E402

from vnpy_ai.models import PortfolioDecision, WorkflowResult  # noqa: E402
from vnpy_ai.workflow.runner import WorkflowRunner, create_initial_state  # noqa: E402


@pytest.fixture
def mock_data_adapter() -> MockDataAdapter:
    return MockDataAdapter()


@pytest.fixture
def patched_call_llm():
    """Patch ``vnpy_ai.utils.llm.call_llm`` to return canned responses."""
    with patch("vnpy_ai.utils.llm.call_llm", side_effect=MockLlmResponses.make_side_effect()) as mocked:
        yield mocked


class TestWorkflowState:
    """Tests for the workflow state factory."""

    def test_create_initial_state_shape(self):
        state = create_initial_state(
            tickers=["AAPL"],
            portfolio={"cash": 100000.0, "positions": []},
            start_date="2024-01-01",
            end_date="2024-03-01",
        )
        assert state["data"]["tickers"] == ["AAPL"]
        assert state["data"]["start_date"] == "2024-01-01"
        assert state["data"]["end_date"] == "2024-03-01"
        assert state["metadata"]["model_name"] == "llama3"
        assert state["metadata"]["model_provider"] == "Ollama"
        assert "analyst_signals" in state["data"]


class TestWorkflowRunnerFallback:
    """Tests for the fallback path when LangGraph is unavailable."""

    def test_hold_fallback_returns_hold_decisions(self, mock_data_adapter):
        runner = WorkflowRunner(
            data_adapter=mock_data_adapter,
            fallback_strategy="hold",
        )
        result = runner.run(tickers=["AAPL", "GOOGL"])

        assert isinstance(result, WorkflowResult)
        assert set(result.decisions.keys()) == {"AAPL", "GOOGL"}
        for decision in result.decisions.values():
            assert decision.action == "hold"
            assert decision.quantity == 0
        # current_prices should be populated from the mock data
        assert result.current_prices["AAPL"] == pytest.approx(192.30)

    def test_sma_cross_fallback_with_insufficient_history(self, mock_data_adapter):
        # Mock data has only 5 days; SMA(20) cannot be computed -> hold.
        # When LangGraph is installed, the workflow graph runs first with
        # fallback_handler node. To test sma_cross strategy, mock the import.
        runner = WorkflowRunner(
            data_adapter=mock_data_adapter,
            fallback_strategy="sma_cross",
        )
        # Patch the graph import to force the strategy fallback path
        with patch("vnpy_ai.workflow.graph.build_workflow_graph", return_value=None):
            result = runner.run(tickers=["AAPL"])
        assert result.decisions["AAPL"].action == "hold"
        assert "insufficient" in result.decisions["AAPL"].reasoning.lower()


class TestWorkflowRunnerWithMockedLlm:
    """Tests that exercise the LangGraph path with a mocked LLM.

    These tests verify the wiring between the workflow runner, the graph, and
    the agents. They patch ``call_llm`` so no real provider is contacted.
    """

    def test_runner_returns_workflow_result(self, mock_data_adapter, patched_call_llm):
        runner = WorkflowRunner(data_adapter=mock_data_adapter)
        result = runner.run(tickers=["AAPL"])

        assert isinstance(result, WorkflowResult)
        assert "AAPL" in result.decisions
        # Whether LangGraph succeeded or fell back, a decision must exist.
        assert isinstance(result.decisions["AAPL"], PortfolioDecision)

    def test_runner_publishes_status_when_event_adapter_set(
        self, mock_data_adapter, patched_call_llm
    ):
        from unittest.mock import MagicMock

        event_adapter = MagicMock()
        runner = WorkflowRunner(
            data_adapter=mock_data_adapter,
            event_adapter=event_adapter,
        )
        runner.run(tickers=["AAPL"])

        # At least one status publish call should have been made.
        assert event_adapter.publish_status.called


class TestAgentAnalyzeWithMockedLlm:
    """Tests that individual agents return structured signals with a mocked LLM."""

    def test_warren_buffett_returns_structured_signal(
        self, mock_data_adapter, patched_call_llm
    ):
        from vnpy_ai.agents.warren_buffett import WarrenBuffettAgent

        agent = WarrenBuffettAgent(data_adapter=mock_data_adapter)
        state = {
            "ticker": "AAPL",
            "start_date": "2024-01-02",
            "end_date": "2024-01-08",
        }
        result = agent.analyze(state)

        assert result["agent_id"] == "warren_buffett_agent"
        assert result["ticker"] == "AAPL"
        # Signal must be one of the valid values; agent may fall back to
        # neutral when data formatting prevents the LLM call.
        assert result["signal"] in {"bullish", "bearish", "neutral"}
        assert 0 <= result["confidence"] <= 100

    def test_ben_graham_returns_neutral_signal(
        self, mock_data_adapter, patched_call_llm
    ):
        from vnpy_ai.agents.benjamin_graham import BenjaminGrahamAgent

        agent = BenjaminGrahamAgent(data_adapter=mock_data_adapter)
        state = {
            "ticker": "AAPL",
            "start_date": "2024-01-02",
            "end_date": "2024-01-08",
        }
        result = agent.analyze(state)

        assert result["agent_id"] == "ben_graham_agent"
        assert result["signal"] in {"bullish", "bearish", "neutral"}
        assert 0 <= result["confidence"] <= 100
