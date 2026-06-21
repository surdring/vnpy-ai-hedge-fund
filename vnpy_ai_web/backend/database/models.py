"""SQLAlchemy ORM models for vnpy_ai_web."""

from __future__ import annotations

from datetime import datetime, UTC

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(64), unique=True, nullable=False, index=True)
    key_prefix = Column(String(8), nullable=False)
    encrypted_key = Column(Text, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class Flow(Base):
    __tablename__ = "flows"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), nullable=False)
    description = Column(Text, default="")
    nodes = Column(JSON, default=list)
    edges = Column(JSON, default=list)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    runs = relationship("FlowRun", back_populates="flow", cascade="all, delete-orphan")


class FlowRun(Base):
    __tablename__ = "flow_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    flow_id = Column(Integer, ForeignKey("flows.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(32), default="pending")  # pending / running / completed / failed
    result = Column(JSON, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    flow = relationship("Flow", back_populates="runs")
