"""
FastAPI backend for the VeighNa AI Hedge Fund workflow editor.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from vnpy_ai_web.backend.routes.api_keys import router as api_keys_router
from vnpy_ai_web.backend.routes.flows import router as flows_router
from vnpy_ai_web.backend.routes.flow_runs import router as flow_runs_router
from vnpy_ai_web.backend.routes.hedge_fund import router as hedge_fund_router
from vnpy_ai_web.backend.routes.language_models import router as language_models_router
from vnpy_ai_web.backend.routes.ollama import router as ollama_router
from vnpy_ai_web.backend.routes.storage import router as storage_router


def create_app() -> FastAPI:
    """Create FastAPI app."""

    app = FastAPI(
        title="VeighNa AI Hedge Fund API",
        description="Backend API for the VeighNa AI Hedge Fund workflow editor",
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include all routers
    app.include_router(api_keys_router)
    app.include_router(flows_router)
    app.include_router(flow_runs_router)
    app.include_router(hedge_fund_router)
    app.include_router(language_models_router)
    app.include_router(ollama_router)
    app.include_router(storage_router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "timestamp": datetime.now().isoformat()}

    @app.get("/metrics")
    async def metrics() -> dict[str, int]:
        return {
            "vnpy_ai_agent_processing_time_ms": 0,
            "vnpy_ai_trade_latency_ms": 0,
            "vnpy_ai_memory_usage_mb": 0,
            "vnpy_ai_workflows_total": 0,
            "vnpy_ai_orders_total": 0,
        }

    return app


app = create_app()
