"""Add user_settings table

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-23
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("api_key_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("api_key.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("settings_json", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_user_settings_api_key_id", "user_settings", ["api_key_id"])


def downgrade() -> None:
    op.drop_index("ix_user_settings_api_key_id", "user_settings")
    op.drop_table("user_settings")
