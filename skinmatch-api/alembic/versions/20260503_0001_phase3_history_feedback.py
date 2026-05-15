"""phase 3 history and feedback

Revision ID: 20260503_0001
Revises:
Create Date: 2026-05-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260503_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "analysis_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_name", sa.String(length=160), nullable=True),
        sa.Column("brand", sa.String(length=120), nullable=True),
        sa.Column("main_goal", sa.String(length=80), nullable=False),
        sa.Column("raw_ingredient_list", sa.Text(), nullable=False),
        sa.Column("skin_profile_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("parsed_formula_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("compatibility_score", sa.Float(), nullable=False),
        sa.Column("verdict", sa.String(length=40), nullable=False),
        sa.Column("irritation_risk", sa.Float(), nullable=False),
        sa.Column("acne_risk", sa.Float(), nullable=False),
        sa.Column("benefit_score", sa.Float(), nullable=False),
        sa.Column("barrier_support", sa.Float(), nullable=False),
        sa.Column("applied_rules", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("positive_ingredients", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("warning_ingredients", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("unknown_ingredients", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("disclaimer", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analysis_records_created_at"), "analysis_records", ["created_at"], unique=False)
    op.create_index(op.f("ix_analysis_records_user_id"), "analysis_records", ["user_id"], unique=False)
    op.create_index(op.f("ix_analysis_records_verdict"), "analysis_records", ["verdict"], unique=False)

    op.create_table(
        "product_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("analysis_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("used_product", sa.Boolean(), nullable=False),
        sa.Column("usage_days", sa.Integer(), nullable=True),
        sa.Column("usage_frequency", sa.Text(), nullable=True),
        sa.Column("irritation_level", sa.Integer(), nullable=False),
        sa.Column("acne_level", sa.Integer(), nullable=False),
        sa.Column("dryness_level", sa.Integer(), nullable=False),
        sa.Column("satisfaction_level", sa.Integer(), nullable=False),
        sa.Column("noticed_benefits", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("would_buy_again", sa.Boolean(), nullable=True),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_id"], ["analysis_records.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("analysis_id", name="uq_product_feedback_analysis_id"),
    )
    op.create_index(op.f("ix_product_feedback_analysis_id"), "product_feedback", ["analysis_id"], unique=False)
    op.create_index(op.f("ix_product_feedback_user_id"), "product_feedback", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_product_feedback_user_id"), table_name="product_feedback")
    op.drop_index(op.f("ix_product_feedback_analysis_id"), table_name="product_feedback")
    op.drop_table("product_feedback")
    op.drop_index(op.f("ix_analysis_records_verdict"), table_name="analysis_records")
    op.drop_index(op.f("ix_analysis_records_user_id"), table_name="analysis_records")
    op.drop_index(op.f("ix_analysis_records_created_at"), table_name="analysis_records")
    op.drop_table("analysis_records")
