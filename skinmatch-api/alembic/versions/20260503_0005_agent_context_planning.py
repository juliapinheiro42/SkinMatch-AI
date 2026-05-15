"""agent context planning

Revision ID: 20260503_0005
Revises: 20260503_0004
Create Date: 2026-05-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260503_0005"
down_revision: str | None = "20260503_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("agent_messages", sa.Column("confidence", sa.String(length=20), nullable=True))
    op.add_column("agent_messages", sa.Column("user_context_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column("agent_messages", "user_context_snapshot")
    op.drop_column("agent_messages", "confidence")
