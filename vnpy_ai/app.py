"""
VeighNa App entrypoint for AI Hedge Fund integration.
"""

from __future__ import annotations

from pathlib import Path

from vnpy.trader.app import BaseApp

from .engine import AiHedgeFundEngine


class AiHedgeFundApp(BaseApp):
    """Register the AI Hedge Fund integration as a VeighNa app."""

    app_name = "AiHedgeFund"
    app_module = __module__.rsplit(".", 1)[0]
    app_path = Path(__file__).parent
    display_name = "AI Hedge Fund"
    engine_class = AiHedgeFundEngine
    widget_name = "AiHedgeFundWidget"
    icon_name = "ai_hedge_fund.ico"

