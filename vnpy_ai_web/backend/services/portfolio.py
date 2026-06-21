"""Portfolio service for managing portfolio data."""

from __future__ import annotations


class PortfolioService:
    """Service for portfolio management."""

    def get_portfolio(self) -> dict:
        """Get current portfolio summary (stub)."""
        return {
            "cash": 100000.0,
            "total_value": 100000.0,
            "margin_used": 0.0,
            "pnl": 0.0,
        }

    def get_positions(self) -> list[dict]:
        """Get current positions (stub)."""
        return []
