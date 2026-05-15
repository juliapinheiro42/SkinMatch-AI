"""phase 8 catalog fields

Revision ID: 20260503_0004
Revises: 20260503_0003
Create Date: 2026-05-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260503_0004"
down_revision: str | None = "20260503_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("products", "raw_ingredient_list", existing_type=sa.Text(), nullable=True)
    op.add_column("products", sa.Column("category", sa.String(length=80), nullable=True))
    op.add_column("products", sa.Column("routine_step", sa.String(length=80), nullable=True))
    op.add_column("products", sa.Column("usage_periods", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"))
    op.add_column("products", sa.Column("price_range", sa.String(length=40), nullable=True))
    op.add_column("products", sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"))
    op.add_column("products", sa.Column("is_active_treatment", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("products", sa.Column("is_sunscreen", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("products", sa.Column("is_moisturizer", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("products", sa.Column("is_cleanser", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("products", sa.Column("source", sa.String(length=80), nullable=True))
    op.add_column("products", sa.Column("source_url", sa.Text(), nullable=True))
    op.add_column("products", sa.Column("catalog_status", sa.String(length=40), nullable=False, server_default="active"))
    op.create_index(op.f("ix_products_category"), "products", ["category"], unique=False)
    op.create_index(op.f("ix_products_routine_step"), "products", ["routine_step"], unique=False)
    op.create_index(op.f("ix_products_price_range"), "products", ["price_range"], unique=False)
    op.create_index(op.f("ix_products_catalog_status"), "products", ["catalog_status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_products_catalog_status"), table_name="products")
    op.drop_index(op.f("ix_products_price_range"), table_name="products")
    op.drop_index(op.f("ix_products_routine_step"), table_name="products")
    op.drop_index(op.f("ix_products_category"), table_name="products")
    op.drop_column("products", "catalog_status")
    op.drop_column("products", "source_url")
    op.drop_column("products", "source")
    op.drop_column("products", "is_cleanser")
    op.drop_column("products", "is_moisturizer")
    op.drop_column("products", "is_sunscreen")
    op.drop_column("products", "is_active_treatment")
    op.drop_column("products", "tags")
    op.drop_column("products", "price_range")
    op.drop_column("products", "usage_periods")
    op.drop_column("products", "routine_step")
    op.drop_column("products", "category")
    op.alter_column("products", "raw_ingredient_list", existing_type=sa.Text(), nullable=False)
