"""Add api_key, watchlist, watchlist_symbol, alert tables; add last_price to analysis_run

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-17
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "api_key",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("key_prefix", sa.String(8), nullable=False),
        sa.Column("key_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "watchlist",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("api_key_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("api_key.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_watchlist_api_key_id", "watchlist", ["api_key_id"])

    op.create_table(
        "watchlist_symbol",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("watchlist_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("watchlist.id", ondelete="CASCADE"), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("watchlist_id", "symbol", name="uq_watchlist_symbol"),
    )
    op.create_index("ix_watchlist_symbol_watchlist_id", "watchlist_symbol", ["watchlist_id"])

    op.create_table(
        "alert",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("api_key_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("api_key.id", ondelete="CASCADE"), nullable=False),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("condition", sa.String(30), nullable=False),
        sa.Column("threshold_value", sa.Float, nullable=True),
        sa.Column("threshold_verdict", sa.String(40), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_alert_api_key_id", "alert", ["api_key_id"])
    op.create_index("ix_alert_symbol", "alert", ["symbol"])

    op.add_column("analysis_run", sa.Column("last_price", sa.Float, nullable=True))


def downgrade() -> None:
    op.drop_column("analysis_run", "last_price")
    op.drop_index("ix_alert_symbol", "alert")
    op.drop_index("ix_alert_api_key_id", "alert")
    op.drop_table("alert")
    op.drop_index("ix_watchlist_symbol_watchlist_id", "watchlist_symbol")
    op.drop_table("watchlist_symbol")
    op.drop_index("ix_watchlist_api_key_id", "watchlist")
    op.drop_table("watchlist")
    op.drop_table("api_key")
