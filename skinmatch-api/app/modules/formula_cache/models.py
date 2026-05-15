from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FormulaAnalysisCache(Base):
    __tablename__ = "formula_analysis_cache"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    formula_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    base_irritation_risk: Mapped[float] = mapped_column(Float, nullable=False)
    base_acne_risk: Mapped[float] = mapped_column(Float, nullable=False)
    base_benefit_score: Mapped[float] = mapped_column(Float, nullable=False)
    base_barrier_support: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
