"""Create analysis_run and agent_artifact tables

Revision ID: 0001
Revises:
Create Date: 2026-05-14
"""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analysis_run",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("instrument_recommendation", sa.String(40), nullable=True),
        sa.Column("confidence_note", sa.Text, nullable=True),
        sa.Column("verdict_json", JSONB, nullable=True),
        sa.Column("portfolio_value_usd", sa.Float, nullable=True),
        sa.Column("max_risk_per_trade_pct", sa.Float, nullable=True),
    )
    op.create_index("ix_analysis_run_symbol", "analysis_run", ["symbol"])
    op.create_index(
        "ix_analysis_run_symbol_started", "analysis_run", ["symbol", "started_at"]
    )

    op.create_table(
        "agent_artifact",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "run_id",
            UUID(as_uuid=True),
            sa.ForeignKey("analysis_run.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("agent_name", sa.String(60), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("latency_ms", sa.Float, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("payload_json", JSONB, nullable=False, server_default="{}"),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_agent_artifact_run_id", "agent_artifact", ["run_id"])


def downgrade() -> None:
    op.drop_table("agent_artifact")
    op.drop_table("analysis_run")
