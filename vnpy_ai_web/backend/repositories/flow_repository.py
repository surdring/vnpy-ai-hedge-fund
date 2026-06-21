"""Repository for Flow CRUD operations."""

from __future__ import annotations

from datetime import datetime, UTC

from sqlalchemy.orm import Session

from vnpy_ai_web.backend.database.models import Flow


class FlowRepository:
    """Repository for Flow model."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, name: str, description: str = "", nodes: list | None = None, edges: list | None = None) -> Flow:
        """Create a new flow."""
        flow = Flow(
            name=name,
            description=description,
            nodes=nodes or [],
            edges=edges or [],
        )
        self._session.add(flow)
        self._session.commit()
        self._session.refresh(flow)
        return flow

    def get_by_id(self, flow_id: int) -> Flow | None:
        """Get a flow by ID."""
        return self._session.query(Flow).filter(Flow.id == flow_id).first()

    def list_all(self) -> list[Flow]:
        """List all flows."""
        return self._session.query(Flow).all()

    def update(self, flow_id: int, **kwargs: object) -> Flow | None:
        """Update a flow."""
        flow = self.get_by_id(flow_id)
        if flow is None:
            return None
        for key, value in kwargs.items():
            if hasattr(flow, key):
                setattr(flow, key, value)
        flow.updated_at = datetime.now(UTC)
        self._session.commit()
        self._session.refresh(flow)
        return flow

    def delete(self, flow_id: int) -> bool:
        """Delete a flow."""
        flow = self.get_by_id(flow_id)
        if flow is None:
            return False
        self._session.delete(flow)
        self._session.commit()
        return True
