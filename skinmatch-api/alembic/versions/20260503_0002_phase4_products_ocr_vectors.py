"""phase 4 products ocr vectors

Revision ID: 20260503_0002
Revises: 20260503_0001
Create Date: 2026-05-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260503_0002"
down_revision: str | None = "20260503_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("brand", sa.String(length=140), nullable=False),
        sa.Column("normalized_name", sa.String(length=340), nullable=False),
        sa.Column("formula_hash", sa.String(length=64), nullable=False),
        sa.Column("raw_ingredient_list", sa.Text(), nullable=False),
        sa.Column("embedding", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute("ALTER TABLE products ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector")
    op.create_index(op.f("ix_products_formula_hash"), "products", ["formula_hash"], unique=True)
    op.create_index(op.f("ix_products_normalized_name"), "products", ["normalized_name"], unique=False)

    op.create_table(
        "product_formulas",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parsed_formula_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_product_formulas_product_id"), "product_formulas", ["product_id"], unique=False)

    op.create_table(
        "formula_analysis_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("formula_hash", sa.String(length=64), nullable=False),
        sa.Column("base_irritation_risk", sa.Float(), nullable=False),
        sa.Column("base_acne_risk", sa.Float(), nullable=False),
        sa.Column("base_benefit_score", sa.Float(), nullable=False),
        sa.Column("base_barrier_support", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_formula_analysis_cache_formula_hash"), "formula_analysis_cache", ["formula_hash"], unique=True)

    op.add_column("analysis_records", sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index(op.f("ix_analysis_records_product_id"), "analysis_records", ["product_id"], unique=False)
    op.create_foreign_key(
        "fk_analysis_records_product_id_products",
        "analysis_records",
        "products",
        ["product_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_analysis_records_product_id_products", "analysis_records", type_="foreignkey")
    op.drop_index(op.f("ix_analysis_records_product_id"), table_name="analysis_records")
    op.drop_column("analysis_records", "product_id")
    op.drop_index(op.f("ix_formula_analysis_cache_formula_hash"), table_name="formula_analysis_cache")
    op.drop_table("formula_analysis_cache")
    op.drop_index(op.f("ix_product_formulas_product_id"), table_name="product_formulas")
    op.drop_table("product_formulas")
    op.drop_index(op.f("ix_products_normalized_name"), table_name="products")
    op.drop_index(op.f("ix_products_formula_hash"), table_name="products")
    op.drop_table("products")
