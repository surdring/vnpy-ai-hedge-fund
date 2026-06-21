"""Repository for FlowRun CRUD operations."""

from __future__ import annotations

from datetime import datetime, UTC

from sqlalchemy.orm import Session

from vnpy_ai_web.backend.database.models import FlowRun


class FlowRunRepository:
    """Repository for FlowRun model."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, flow_id: int) -> FlowRun:
        """Create a new flow run."""
        run = FlowRun(flow_id=flow_id, status="pending")
        self._session.add(run)
        self._session.commit()
        self._session.refresh(run)
        return run

    def get_by_id(self, run_id: int) -> FlowRun | None:
        """Get a flow run by ID."""
        return self._session.query(FlowRun).filter(FlowRun.id == run_id).first()

    def list_by_flow(self, flow_id: int) -> list[FlowRun]:
        """List all runs for a flow."""
        return self._session.query(FlowRun).filter(FlowRun.flow_id == flow_id).all()

    def list_all(self) -> list[FlowRun]:
        """List all flow runs."""
        return self._session.query(FlowRun).all()

    def update_status(self, run_id: int, status: str, result: dict | None = None) -> FlowRun | None:
        """Update the status of a flow run."""
        run = self.get_by_id(run_id)
        if run is None:
            return None
        run.status = status
        if result is not None:
            run.result = result
        if status == "running" and run.started_at is None:
            run.started_at = datetime.now(UTC)
        if status in ("completed", "failed"):
            run.completed_at = datetime.now(UTC)
        self._session.commit()
        self._session.refresh(run)
        return run

    def delete(self, run_id: int) -> bool:
        """Delete a flow run."""
        run = self.get_by_id(run_id)
        if run is None:
            return False
        self._session.delete(run)
        self._session.commit()
        return True
