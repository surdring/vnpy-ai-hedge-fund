"""
Event adapter for publishing AI workflow output to VeighNa EventEngine.
"""

from __future__ import annotations

from typing import Any

from vnpy.event import Event, EventEngine
from vnpy.trader.event import EVENT_LOG
from vnpy.trader.object import LogData

from .models import AnalystSignal, PortfolioDecision, WorkflowResult


try:
    from vnpy.trader.event import EVENT_AI_SIGNAL, EVENT_AI_DECISION, EVENT_AI_DECISION_ORDER, EVENT_AI_ERROR, EVENT_AI_STATUS
except ImportError:
    EVENT_AI_SIGNAL = "eAiSignal"
    EVENT_AI_DECISION = "eAiDecision"
    EVENT_AI_DECISION_ORDER = "eAiDecisionOrder"
    EVENT_AI_ERROR = "eAiError"
    EVENT_AI_STATUS = "eAiStatus"


class EventAdapter:
    """Publish normalized AI events into VeighNa."""

    def __init__(self, event_engine: EventEngine) -> None:
        self.event_engine = event_engine

    def publish_signal(self, signal: AnalystSignal) -> None:
        self.event_engine.put(Event(EVENT_AI_SIGNAL, signal))

    def publish_decision(self, decision: PortfolioDecision) -> None:
        self.event_engine.put(Event(EVENT_AI_DECISION, decision))

    def publish_order_decision(self, payload: Any) -> None:
        self.event_engine.put(Event(EVENT_AI_DECISION_ORDER, payload))

    def publish_error(self, message: str, agent: str | None = None) -> None:
        payload = {"message": message, "agent": agent}
        self.event_engine.put(Event(EVENT_AI_ERROR, payload))
        self.event_engine.put(Event(EVENT_LOG, LogData(msg=message, gateway_name="AiHedgeFund")))

    def publish_status(self, status: str, agent: str | None = None, progress: float | None = None, message: str = "") -> None:
        self.event_engine.put(Event(EVENT_AI_STATUS, {"agent": agent, "status": status, "progress": progress, "message": message}))

    def publish_workflow_result(self, result: WorkflowResult) -> None:
        for decision in result.decisions.values():
            self.publish_decision(decision)

    def convert_and_publish(self, workflow_result: WorkflowResult) -> None:
        """Extract decisions from WorkflowResult and publish as AiSignalData/AiDecisionData.

        For each decision in the workflow result, creates the appropriate VeighNa
        dataclass and publishes via EVENT_AI_SIGNAL or EVENT_AI_DECISION.
        """
        try:
            from vnpy.trader.object import AiSignalData, AiDecisionData
        except ImportError:
            AiSignalData = None  # type: ignore[assignment]
            AiDecisionData = None  # type: ignore[assignment]

        # Publish analyst signals as AiSignalData
        for agent_key, signals in workflow_result.analyst_signals.items():
            for ticker, sig_data in (signals or {}).items():
                if not isinstance(sig_data, dict):
                    continue
                try:
                    if AiSignalData is not None:
                        data = AiSignalData(
                            agent_name=agent_key,
                            ticker=ticker,
                            signal=sig_data.get("signal", "neutral"),
                            confidence=float(sig_data.get("confidence", 0)),
                            reasoning=sig_data.get("reasoning"),
                        )
                        self.event_engine.put(Event(EVENT_AI_SIGNAL, data))
                    else:
                        self.publish_signal(
                            AnalystSignal(
                                agent_name=agent_key,
                                ticker=ticker,
                                signal=sig_data.get("signal", "neutral"),
                                confidence=float(sig_data.get("confidence", 0)),
                                reasoning=sig_data.get("reasoning"),
                            )
                        )
                except Exception:
                    pass

        # Publish portfolio decisions as AiDecisionData
        for ticker, decision in workflow_result.decisions.items():
            try:
                if AiDecisionData is not None:
                    data = AiDecisionData(
                        ticker=ticker,
                        action=decision.action,
                        quantity=decision.quantity,
                        confidence=decision.confidence,
                        reasoning=decision.reasoning,
                    )
                    self.event_engine.put(Event(EVENT_AI_DECISION, data))
                else:
                    self.publish_decision(decision)
            except Exception:
                pass
