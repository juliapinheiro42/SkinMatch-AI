from sqlalchemy.orm import Session

from app.modules.analysis.engine import calculate_base_formula
from app.modules.formula_cache.models import FormulaAnalysisCache
from app.modules.formula_cache.repository import create_formula_cache, get_formula_cache


def get_or_create_formula_cache(db: Session, formula_hash: str, parsed_ingredients: list[dict]) -> FormulaAnalysisCache:
    cached = get_formula_cache(db, formula_hash)
    if cached:
        return cached

    base = calculate_base_formula(parsed_ingredients)
    return create_formula_cache(
        db,
        formula_hash=formula_hash,
        base_irritation_risk=base["base_irritation_risk"],
        base_acne_risk=base["base_acne_risk"],
        base_benefit_score=base["base_benefit_score"],
        base_barrier_support=base["base_barrier_support"],
    )
