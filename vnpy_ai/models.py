"""
Shared models for the VeighNa AI Hedge Fund integration.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


AiAction = Literal["buy", "sell", "short", "cover", "hold"]


class Price(BaseModel):
    """AI Hedge Fund compatible OHLCV price model."""

    open: float
    close: float
    high: float
    low: float
    volume: int
    time: str


class FinancialMetrics(BaseModel):
    """Financial metrics placeholder compatible with AI Hedge Fund agents."""

    ticker: str
    report_period: str
    period: str = "ttm"
    currency: str = "USD"
    market_cap: float | None = None
    price_to_earnings_ratio: float | None = None
    price_to_book_ratio: float | None = None
    return_on_equity: float | None = None


class CompanyNews(BaseModel):
    """Company news placeholder compatible with AI Hedge Fund agents."""

    ticker: str
    title: str
    source: str
    date: str
    url: str
    author: str | None = None
    sentiment: str | None = None


class InsiderTrade(BaseModel):
    """Insider trade placeholder compatible with AI Hedge Fund agents."""

    ticker: str
    filing_date: str
    issuer: str | None = None
    name: str | None = None
    transaction_shares: float | None = None
    transaction_price_per_share: float | None = None


class AnalystSignal(BaseModel):
    """Normalized signal emitted by an analyst agent."""

    agent_name: str
    ticker: str
    signal: str
    confidence: float = 0
    reasoning: dict[str, Any] | str | None = None
    timestamp: datetime = Field(default_factory=datetime.now)


class PortfolioDecision(BaseModel):
    """Single ticker decision emitted by portfolio management."""

    ticker: str
    action: AiAction = "hold"
    quantity: int = 0
    confidence: float = 0
    reasoning: str = "Fallback decision: hold"
    price: float | None = None


class WorkflowResult(BaseModel):
    """Result returned by the integration workflow."""

    decisions: dict[str, PortfolioDecision]
    analyst_signals: dict[str, dict[str, Any]] = Field(default_factory=dict)
    current_prices: dict[str, float] = Field(default_factory=dict)
    degraded: bool = False
    error: str | None = None


class RpcMessage(BaseModel):
    """Uniform JSON-serializable RPC message wrapper."""

    type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    request_id: str = Field(default_factory=lambda: uuid4().hex)
    timestamp: datetime = Field(default_factory=datetime.now)
    error_code: int | None = None
    error_message: str | None = None


class AgentStatus(BaseModel):
    """Runtime status for the AI engine and agent process."""

    enabled: bool = False
    auto_trading: bool = False
    agent_process_alive: bool = False
    rpc_connected: bool = False
    last_error: str | None = None


def mask_secret(value: str | None) -> str | None:
    """Mask a secret for UI/API responses."""

    if value is None:
        return None
    if len(value) <= 7:
        return "****"
    return f"{value[:3]}****{value[-4:]}"

