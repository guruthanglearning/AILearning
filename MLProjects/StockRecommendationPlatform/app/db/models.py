from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class AnalysisRun(Base):
    __tablename__ = "analysis_run"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="running")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    instrument_recommendation: Mapped[str | None] = mapped_column(String(40))
    confidence_note: Mapped[str | None] = mapped_column(Text)
    verdict_json: Mapped[dict | None] = mapped_column(JSONB)
    portfolio_value_usd: Mapped[float | None] = mapped_column()
    max_risk_per_trade_pct: Mapped[float | None] = mapped_column()

    artifacts: Mapped[list[AgentArtifact]] = relationship(
        "AgentArtifact", back_populates="run", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_analysis_run_symbol_started", "symbol", "started_at"),)


class AgentArtifact(Base):
    __tablename__ = "agent_artifact"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analysis_run.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_name: Mapped[str] = mapped_column(String(60), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    latency_ms: Mapped[float | None] = mapped_column()
    error_message: Mapped[str | None] = mapped_column(Text)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    run: Mapped[AnalysisRun] = relationship("AnalysisRun", back_populates="artifacts")
