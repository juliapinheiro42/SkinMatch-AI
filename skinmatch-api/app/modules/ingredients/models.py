from sqlalchemy import Float, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    inci_name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    synonyms: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    irritation_risk: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    acne_risk: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    benefit_acne: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    benefit_oil_control: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    benefit_barrier: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
