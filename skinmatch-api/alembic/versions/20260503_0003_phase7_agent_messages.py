"""phase 7 agent messages

Revision ID: 20260503_0003
Revises: 20260503_0002
Create Date: 2026-05-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260503_0003"
down_revision: str | None = "20260503_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("intent", sa.String(length=80), nullable=True),
        sa.Column("tools_used", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("structured_result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agent_messages_created_at"), "agent_messages", ["created_at"], unique=False)
    op.create_index(op.f("ix_agent_messages_intent"), "agent_messages", ["intent"], unique=False)
    op.create_index(op.f("ix_agent_messages_user_id"), "agent_messages", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_agent_messages_user_id"), table_name="agent_messages")
    op.drop_index(op.f("ix_agent_messages_intent"), table_name="agent_messages")
    op.drop_index(op.f("ix_agent_messages_created_at"), table_name="agent_messages")
    op.drop_table("agent_messages")
