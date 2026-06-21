"""Hedge fund routes — run and backtest endpoints."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from vnpy_ai.agents import get_agents_list
from vnpy_ai.data_adapter import DataAdapter
from vnpy_ai.workflow.runner import WorkflowRunner

router = APIRouter(prefix="/hedge-fund", tags=["hedge-fund"])


class HedgeFundRequest(BaseModel):
    """Request model for hedge fund analysis."""

    tickers: list[str]
    start_date: str | None = None
    end_date: str | None = None
    initial_cash: float = 100000.0
    model_name: str = "llama3"
    model_provider: str = "Ollama"
    graph_nodes: list[dict] = Field(default_factory=list)
    graph_edges: list[dict] = Field(default_factory=list)
    api_keys: dict[str, str] | None = None


@router.get("/agents")
async def agents() -> dict[str, list[dict]]:
    """List available hedge fund agents."""
    return {"agents": get_agents_list()}


@router.post("/run")
async def run(request: HedgeFundRequest) -> StreamingResponse:
    """Run hedge fund analysis workflow."""
    async def event_generator() -> AsyncIterator[str]:
        yield _sse("start", {"message": "started"})
        portfolio = {
            "cash": request.initial_cash,
            "margin_requirement": 0.0,
            "margin_used": 0.0,
            "positions": {
                ticker: {
                    "long": 0,
                    "short": 0,
                    "long_cost_basis": 0.0,
                    "short_cost_basis": 0.0,
                    "short_margin_used": 0.0,
                }
                for ticker in request.tickers
            },
            "realized_gains": {ticker: {"long": 0.0, "short": 0.0} for ticker in request.tickers},
        }
        runner = WorkflowRunner(DataAdapter())
        result = runner.run(
            request.tickers,
            portfolio=portfolio,
            start_date=request.start_date,
            end_date=request.end_date,
            model_name=request.model_name,
            model_provider=request.model_provider,
        )
        yield _sse("progress", {"agent": "fallback", "status": "Done"})
        yield _sse("complete", {"data": result.model_dump(mode="json")})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/backtest")
async def run_backtest(request: dict) -> StreamingResponse:
    """Run backtest and return SSE streaming progress."""
    async def event_stream() -> AsyncIterator[str]:
        yield f"data: {json.dumps({'status': 'started', 'progress': 0})}\n\n"
        for i in range(1, 6):
            await asyncio.sleep(1)
            yield f"data: {json.dumps({'status': 'running', 'progress': i * 20})}\n\n"
        yield f"data: {json.dumps({'status': 'complete', 'progress': 100})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
