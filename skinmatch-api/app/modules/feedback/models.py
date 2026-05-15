from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.modules.analysis_records.models import AnalysisRecord


class ProductFeedback(Base):
    __tablename__ = "product_feedback"
    __table_args__ = (UniqueConstraint("analysis_id", name="uq_product_feedback_analysis_id"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    analysis_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("analysis_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    used_product: Mapped[bool] = mapped_column(Boolean, nullable=False)
    usage_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    usage_frequency: Mapped[str | None] = mapped_column(Text, nullable=True)
    irritation_level: Mapped[int] = mapped_column(Integer, nullable=False)
    acne_level: Mapped[int] = mapped_column(Integer, nullable=False)
    dryness_level: Mapped[int] = mapped_column(Integer, nullable=False)
    satisfaction_level: Mapped[int] = mapped_column(Integer, nullable=False)
    noticed_benefits: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    would_buy_again: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    analysis: Mapped["AnalysisRecord"] = relationship("AnalysisRecord", back_populates="feedback")
