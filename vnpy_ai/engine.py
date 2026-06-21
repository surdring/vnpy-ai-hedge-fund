"""
Main VeighNa engine for the AI Hedge Fund integration.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from vnpy.event import Event
from vnpy.trader.engine import BaseEngine, MainEngine
from vnpy.trader.event import EVENT_BAR, EVENT_TICK

from .config import AiSettings, load_settings
from .data_adapter import DataAdapter
from .event_adapter import EventAdapter
from .models import AgentStatus, PortfolioDecision, WorkflowResult
from .monitoring import is_port_open
from .order_adapter import OrderAdapter
from .workflow.runner import WorkflowRunner


APP_NAME = "AiHedgeFund"


class AiHedgeFundEngine(BaseEngine):
    """Coordinate data, events, workflow execution and order submission."""

    def __init__(self, main_engine: MainEngine, event_engine: Any) -> None:
        super().__init__(main_engine, event_engine, APP_NAME)
        self.settings: AiSettings = load_settings()
        self.data_adapter = DataAdapter(main_engine)
        self.event_adapter = EventAdapter(event_engine)
        self.order_adapter = OrderAdapter(main_engine, self.settings.gateway_name)
        self.workflow_runner = WorkflowRunner(self.data_adapter, self.settings.selected_analysts, self.event_adapter, self.settings.fallback_strategy)
        self.status = AgentStatus(enabled=self.settings.enabled, auto_trading=self.settings.enable_auto_trading)
        self._last_result: WorkflowResult | None = None
        self.register_event()

    def register_event(self) -> None:
        """Register market data triggers."""

        self.event_engine.register(EVENT_TICK, self.on_market_event)
        self.event_engine.register(EVENT_BAR, self.on_market_event)

    def set_config(self, settings: AiSettings | dict[str, Any]) -> None:
        """Update runtime settings."""

        self.settings = settings if isinstance(settings, AiSettings) else AiSettings(**settings)
        self.status.enabled = self.settings.enabled
        self.status.auto_trading = self.settings.enable_auto_trading
        self.order_adapter.gateway_name = self.settings.gateway_name
        self.workflow_runner = WorkflowRunner(self.data_adapter, self.settings.selected_analysts, self.event_adapter, self.settings.fallback_strategy)

    def get_status(self) -> AgentStatus:
        """Return current runtime status."""

        self.status.agent_process_alive = is_port_open(self.settings.rpc_host, self.settings.rpc_agent_port)
        return self.status

    def start_agent_process(self) -> bool:
        """Mark agent process as enabled.

        The actual external process launcher is intentionally left to deployment
        scripts so importing vnpy does not load optional LangChain dependencies.
        """

        self.status.enabled = True
        return True

    def stop_agent_process(self) -> None:
        """Disable the agent process integration flag."""

        self.status.enabled = False

    def sync_portfolio(self, tickers: list[str] | None = None) -> dict[str, Any]:
        """Synchronize portfolio from VeighNa."""

        return self.data_adapter.get_portfolio(tickers)

    def run_workflow(
        self,
        tickers: list[str],
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> WorkflowResult:
        """Run one AI decision cycle."""

        try:
            portfolio = self.sync_portfolio(tickers)
            result = self.workflow_runner.run(
                tickers=tickers,
                portfolio=portfolio,
                start_date=start_date,
                end_date=end_date,
                model_name=self.settings.llm_model_name,
                model_provider=self.settings.llm_provider,
            )
            self._last_result = result
            self.event_adapter.publish_workflow_result(result)
            if self.settings.enable_auto_trading:
                for decision in result.decisions.values():
                    self.submit_decision(decision)
            return result
        except Exception as exc:
            self.status.last_error = str(exc)
            self.event_adapter.publish_error(str(exc), APP_NAME)
            fallback = WorkflowResult(
                decisions={ticker: PortfolioDecision(ticker=ticker) for ticker in tickers},
                degraded=True,
                error=str(exc),
            )
            self._last_result = fallback
            return fallback

    def submit_decision(self, decision: PortfolioDecision) -> str:
        """Submit or publish a portfolio decision."""

        if not self.settings.enable_auto_trading:
            self.event_adapter.publish_decision(decision)
            return ""
        orderid = self.order_adapter.send_decision(decision)
        self.event_adapter.publish_order_decision({"orderid": orderid, "decision": decision.model_dump()})
        return orderid

    def on_market_event(self, event: Event) -> None:
        """Handle market data triggers."""

        if not self.settings.enabled:
            return
        data = event.data
        vt_symbol = getattr(data, "vt_symbol", None)
        if not vt_symbol:
            return
        now = datetime.now()
        freq = self.settings.trigger_frequency
        if freq == "daily":
            today = now.date()
            if getattr(self, "_last_trigger_date", None) == today:
                return
            self._last_trigger_date = today
        elif freq in {"tick", "bar"}:
            cooldown = self.settings.signal_cooldown
            last_time = getattr(self, "_last_trigger_time", None)
            if last_time and (now - last_time).total_seconds() < cooldown:
                return
            self._last_trigger_time = now
        self.run_workflow([vt_symbol])

    def send_notification(self, title: str, body: str) -> bool:
        """Send notification via email/wechat if configured.

        Returns True if notification was sent, False otherwise.
        """

        try:
            if hasattr(self, "main_engine") and self.main_engine:
                # Try vnpy email engine
                if hasattr(self.main_engine, "email_engine"):
                    self.main_engine.email_engine.send(title, body)
                    return True
        except Exception:
            pass
        return False

    def close(self) -> None:
        """Clean up engine resources."""

        self.stop_agent_process()

