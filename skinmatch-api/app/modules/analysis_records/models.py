from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AnalysisRecord(Base):
    __tablename__ = "analysis_records"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    product_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    product_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(120), nullable=True)
    main_goal: Mapped[str] = mapped_column(String(80), nullable=False)
    raw_ingredient_list: Mapped[str] = mapped_column(Text, nullable=False)
    skin_profile_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    parsed_formula_snapshot: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    compatibility_score: Mapped[float] = mapped_column(Float, nullable=False)
    verdict: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    irritation_risk: Mapped[float] = mapped_column(Float, nullable=False)
    acne_risk: Mapped[float] = mapped_column(Float, nullable=False)
    benefit_score: Mapped[float] = mapped_column(Float, nullable=False)
    barrier_support: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    applied_rules: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    positive_ingredients: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    warning_ingredients: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    unknown_ingredients: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    disclaimer: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    feedback = relationship(
        "ProductFeedback",
        back_populates="analysis",
        uselist=False,
        cascade="all, delete-orphan",
    )
