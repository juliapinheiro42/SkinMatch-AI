from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.vector import Vector


class Product(Base):
    __tablename__ = "products"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    brand: Mapped[str] = mapped_column(String(140), nullable=False, default="Unknown")
    normalized_name: Mapped[str] = mapped_column(String(340), nullable=False, index=True)
    formula_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    raw_ingredient_list: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    category: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    routine_step: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    usage_periods: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    price_range: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    tags: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    is_active_treatment: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_sunscreen: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_moisturizer: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_cleanser: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    source: Mapped[str | None] = mapped_column(String(80), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    catalog_status: Mapped[str] = mapped_column(String(40), nullable=False, default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    formulas = relationship("ProductFormula", back_populates="product", cascade="all, delete-orphan")


class ProductFormula(Base):
    __tablename__ = "product_formulas"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parsed_formula_snapshot: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)

    product: Mapped[Product] = relationship("Product", back_populates="formulas")
