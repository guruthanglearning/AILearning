from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class BatchJob(Base):
    __tablename__ = "batch_job"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    universe: Mapped[str] = mapped_column(String(20), nullable=False)
    ranking_method: Mapped[str] = mapped_column(String(20), nullable=False, default="weight")
    composition_as_of: Mapped[date | None] = mapped_column(Date, nullable=True)
    total_symbols: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_symbols: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_symbols: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    batch_key: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    symbols_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    runs: Mapped[list["AnalysisRun"]] = relationship("AnalysisRun", back_populates="batch_job")


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
    batch_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("batch_job.id"), nullable=True, index=True
    )

    artifacts: Mapped[list[AgentArtifact]] = relationship(
        "AgentArtifact", back_populates="run", cascade="all, delete-orphan"
    )
    batch_job: Mapped["BatchJob | None"] = relationship("BatchJob", back_populates="runs")

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
