from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.formula_cache.models import FormulaAnalysisCache


def get_formula_cache(db: Session, formula_hash: str) -> FormulaAnalysisCache | None:
    return db.scalar(select(FormulaAnalysisCache).where(FormulaAnalysisCache.formula_hash == formula_hash))


def create_formula_cache(
    db: Session,
    formula_hash: str,
    base_irritation_risk: float,
    base_acne_risk: float,
    base_benefit_score: float,
    base_barrier_support: float,
) -> FormulaAnalysisCache:
    cache = FormulaAnalysisCache(
        formula_hash=formula_hash,
        base_irritation_risk=base_irritation_risk,
        base_acne_risk=base_acne_risk,
        base_benefit_score=base_benefit_score,
        base_barrier_support=base_barrier_support,
    )
    db.add(cache)
    db.commit()
    db.refresh(cache)
    return cache
