"""Add portfolio_position table

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-10
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "portfolio_position",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("api_key_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("api_key.id", ondelete="CASCADE"), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("shares", sa.Float, nullable=False),
        sa.Column("cost_basis", sa.Float, nullable=False),
        sa.Column("entry_date", sa.Date, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_portfolio_position_api_key_id", "portfolio_position", ["api_key_id"])


def downgrade() -> None:
    op.drop_index("ix_portfolio_position_api_key_id", "portfolio_position")
    op.drop_table("portfolio_position")
