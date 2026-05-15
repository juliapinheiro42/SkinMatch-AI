from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserIngredientAffinity(Base):
    __tablename__ = "user_ingredient_affinity"
    __table_args__ = (UniqueConstraint("user_id", "ingredient_name", name="uq_user_ingredient_affinity"),)

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    ingredient_name: Mapped[str] = mapped_column(String(180), nullable=False, index=True)
    tolerance_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    irritation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    acne_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    positive_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    neutral_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
