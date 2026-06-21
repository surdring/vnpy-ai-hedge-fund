"""Mock LLM responses for integration tests.

Provides canned structured outputs keyed by agent name so that tests can
patch ``vnpy_ai.utils.llm.call_llm`` to return deterministic results without
hitting a real LLM provider.
"""

from __future__ import annotations

from typing import Any, Callable

from vnpy_ai.utils.llm import create_default_response


# Canned responses keyed by agent_id. Each value is a dict of kwargs that will
# be passed to the agent's Pydantic signal model. Tests can either:
#   1. Patch ``call_llm`` to return ``MockLlmResponses.for_agent(agent_id)``
#      directly (when the Pydantic model is not needed), or
#   2. Use ``MockLlmResponses.patch_call_llm`` to install a side_effect that
#      constructs the correct Pydantic model instance.
MOCK_RESPONSES: dict[str, dict[str, Any]] = {
    "warren_buffett_agent": {
        "signal": "bullish",
        "confidence": 85,
        "reasoning": "Strong moat and consistent earnings growth.",
    },
    "charlie_munger_agent": {
        "signal": "bullish",
        "confidence": 80,
        "reasoning": "High-quality business at reasonable price.",
    },
    "ben_graham_agent": {
        "signal": "neutral",
        "confidence": 50,
        "reasoning": "Price above intrinsic value.",
    },
    "peter_lynch_agent": {
        "signal": "bullish",
        "confidence": 75,
        "reasoning": "Steady grower with reasonable PEG ratio.",
    },
    "cathie_wood_agent": {
        "signal": "bullish",
        "confidence": 90,
        "reasoning": "Disruptive innovation thesis intact.",
    },
    "phil_fisher_agent": {
        "signal": "bullish",
        "confidence": 78,
        "reasoning": "Strong R&D and management quality.",
    },
    "stanley_druckenmiller_agent": {
        "signal": "bullish",
        "confidence": 82,
        "reasoning": "Favorable macro tailwinds.",
    },
    "bill_ackman_agent": {
        "signal": "bullish",
        "confidence": 77,
        "reasoning": "Activist catalyst unlocking value.",
    },
    "michael_burry_agent": {
        "signal": "bearish",
        "confidence": 65,
        "reasoning": "Valuation stretched; mean reversion likely.",
    },
    "mohnish_pabrai_agent": {
        "signal": "bullish",
        "confidence": 70,
        "reasoning": "Low-risk bet with few bets, big bets.",
    },
    "rakesh_jhunjhunwala_agent": {
        "signal": "bullish",
        "confidence": 73,
        "reasoning": "Growth story intact.",
    },
    "aswath_damodaran_agent": {
        "signal": "neutral",
        "confidence": 55,
        "reasoning": "Intrinsic value close to market price.",
    },
    "nassim_taleb_agent": {
        "signal": "neutral",
        "confidence": 40,
        "reasoning": "Tail risks non-negligible; barbell advised.",
    },
    "fundamentals_analyst_agent": {
        "signal": "bullish",
        "confidence": 72,
        "reasoning": "Solid balance sheet and margins.",
    },
    "sentiment_analyst_agent": {
        "signal": "bullish",
        "confidence": 68,
        "reasoning": "Positive news flow.",
    },
    "technical_analyst_agent": {
        "signal": "bullish",
        "confidence": 71,
        "reasoning": "Above key moving averages.",
    },
    "valuation_analyst_agent": {
        "signal": "neutral",
        "confidence": 52,
        "reasoning": "Fairly valued on DCF.",
    },
    "growth_analyst_agent": {
        "signal": "bullish",
        "confidence": 76,
        "reasoning": "Revenue growth accelerating.",
    },
    "news_sentiment_analyst_agent": {
        "signal": "bullish",
        "confidence": 69,
        "reasoning": "Favorable media coverage.",
    },
    "portfolio_manager_agent": {
        "decisions": [
            {
                "ticker": "AAPL",
                "action": "buy",
                "quantity": 100,
                "confidence": 80,
                "reasoning": "Aggregate bullish signal.",
            },
            {
                "ticker": "GOOGL",
                "action": "hold",
                "quantity": 0,
                "confidence": 50,
                "reasoning": "Mixed signals; wait for clarity.",
            },
        ]
    },
}


class MockLlmResponses:
    """Helper for serving canned LLM responses in tests."""

    @staticmethod
    def for_agent(agent_id: str) -> dict[str, Any]:
        """Return the canned response dict for an agent, or a neutral default."""
        if agent_id in MOCK_RESPONSES:
            return dict(MOCK_RESPONSES[agent_id])
        return {"signal": "neutral", "confidence": 50, "reasoning": "mock default"}

    @staticmethod
    def make_side_effect() -> Callable[..., Any]:
        """Build a side_effect for ``call_llm`` that constructs the Pydantic model.

        The side_effect inspects the ``pydantic_model`` argument and the
        ``agent_name`` keyword to build a properly typed instance from the
        canned response dict. Fields not present in the canned dict fall back
        to the model's defaults via ``create_default_response``.
        """

        def _side_effect(
            prompt: Any,
            pydantic_model: type,
            agent_name: str | None = None,
            state: dict[str, Any] | None = None,
            max_retries: int = 3,
            default_factory: Callable[[], Any] | None = None,
        ) -> Any:
            canned = MockLlmResponses.for_agent(agent_name or "")
            try:
                return pydantic_model(**canned)
            except Exception:
                # If the canned fields don't match the model (e.g. portfolio
                # manager uses a different schema), fall back to defaults.
                return create_default_response(pydantic_model)

        return _side_effect
