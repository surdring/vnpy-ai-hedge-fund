"""Agent base class providing unified data fetching interface."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from vnpy_ai.data_adapter import DataAdapter


class AgentBase:
    """Base class for all AI analyst agents.

    Provides unified data fetching methods that delegate to DataAdapter.
    All analyst agents should inherit from this class.
    """

    agent_id: str = ""
    agent_name: str = ""

    def __init__(self, data_adapter: DataAdapter) -> None:
        self._data_adapter = data_adapter

    def get_prices(
        self, ticker: str, start_date: str, end_date: str
    ) -> list[dict[str, Any]]:
        """Fetch historical price data for a ticker."""
        return cast(list[dict[str, Any]], self._data_adapter.get_prices(ticker, start_date, end_date))

    def get_financial_metrics(self, ticker: str) -> list[dict[str, Any]]:
        """Fetch financial metrics for a ticker.

        Returns empty list if data is unavailable.
        """
        return self._data_adapter.get_financial_metrics(ticker)

    def get_company_news(self, ticker: str) -> list[dict[str, Any]]:
        """Fetch company news for a ticker.

        Returns empty list if data is unavailable.
        """
        return self._data_adapter.get_company_news(ticker)

    def get_portfolio(self) -> dict[str, Any]:
        """Fetch current portfolio state."""
        return self._data_adapter.get_portfolio()

    def analyze(self, state: dict[str, Any]) -> dict[str, Any]:
        """Override in subclasses to implement agent-specific analysis.

        Args:
            state: The current workflow state dict.

        Returns:
            Dict with agent_id and analysis results.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement analyze()"
        )
