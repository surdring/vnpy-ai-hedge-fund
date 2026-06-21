"""
Data fetching tools for the VeighNa AI Hedge Fund integration.

Adapted from ai-hedge-fund/src/tools/api.py (MIT License, Virat Singh).
All data access is delegated to a `DataAdapter` instance injected via
`set_data_adapter()` instead of calling the Financial Datasets API directly.
"""

from vnpy_ai.tools.api import (
    get_financial_metrics,
    get_market_cap,
    get_prices,
    prices_to_df,
    search_line_items,
    set_data_adapter,
)

__all__ = [
    "get_financial_metrics",
    "get_market_cap",
    "get_prices",
    "prices_to_df",
    "search_line_items",
    "set_data_adapter",
]
