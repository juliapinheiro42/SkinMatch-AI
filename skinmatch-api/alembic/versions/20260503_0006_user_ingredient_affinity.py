"""add user ingredient affinity"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "20260503_0006"
down_revision = "20260503_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_ingredient_affinity",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ingredient_name", sa.String(length=180), nullable=False),
        sa.Column("tolerance_score", sa.Float(), nullable=False),
        sa.Column("irritation_count", sa.Integer(), nullable=False),
        sa.Column("acne_count", sa.Integer(), nullable=False),
        sa.Column("positive_count", sa.Integer(), nullable=False),
        sa.Column("neutral_count", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "ingredient_name", name="uq_user_ingredient_affinity"),
    )
    op.create_index(op.f("ix_user_ingredient_affinity_user_id"), "user_ingredient_affinity", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_user_ingredient_affinity_ingredient_name"),
        "user_ingredient_affinity",
        ["ingredient_name"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_user_ingredient_affinity_ingredient_name"), table_name="user_ingredient_affinity")
    op.drop_index(op.f("ix_user_ingredient_affinity_user_id"), table_name="user_ingredient_affinity")
    op.drop_table("user_ingredient_affinity")
