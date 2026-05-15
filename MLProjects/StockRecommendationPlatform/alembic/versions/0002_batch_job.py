"""Add batch_job table and batch_job_id FK on analysis_run

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-14
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "batch_job",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("universe", sa.String(20), nullable=False),
        sa.Column("ranking_method", sa.String(20), nullable=False, server_default="weight"),
        sa.Column("composition_as_of", sa.Date, nullable=True),
        sa.Column("total_symbols", sa.Integer, nullable=False),
        sa.Column("completed_symbols", sa.Integer, nullable=False, server_default="0"),
        sa.Column("failed_symbols", sa.Integer, nullable=False, server_default="0"),
        sa.Column("batch_key", sa.String(100), nullable=True, unique=True),
        sa.Column("symbols_json", postgresql.JSONB, nullable=True),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.add_column(
        "analysis_run",
        sa.Column(
            "batch_job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("batch_job.id"),
            nullable=True,
        ),
    )
    op.create_index("ix_analysis_run_batch_job_id", "analysis_run", ["batch_job_id"])


def downgrade() -> None:
    op.drop_index("ix_analysis_run_batch_job_id", "analysis_run")
    op.drop_column("analysis_run", "batch_job_id")
    op.drop_table("batch_job")
