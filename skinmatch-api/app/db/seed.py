from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.ingredients.models import Ingredient


SEED_INGREDIENTS = [
    {"inci_name": "niacinamide", "synonyms": [], "category": "active", "irritation_risk": 0.05, "acne_risk": 0.02, "benefit_acne": 0.45, "benefit_oil_control": 0.55, "benefit_barrier": 0.35},
    {"inci_name": "salicylic acid", "synonyms": ["bha"], "category": "exfoliant", "irritation_risk": 0.35, "acne_risk": 0.02, "benefit_acne": 0.85, "benefit_oil_control": 0.7, "benefit_barrier": 0.0},
    {"inci_name": "glycolic acid", "synonyms": [], "category": "exfoliant", "irritation_risk": 0.55, "acne_risk": 0.04, "benefit_acne": 0.35, "benefit_oil_control": 0.25, "benefit_barrier": 0.0},
    {"inci_name": "lactic acid", "synonyms": [], "category": "exfoliant", "irritation_risk": 0.35, "acne_risk": 0.03, "benefit_acne": 0.25, "benefit_oil_control": 0.15, "benefit_barrier": 0.1},
    {"inci_name": "retinol", "synonyms": [], "category": "retinoid", "irritation_risk": 0.55, "acne_risk": 0.08, "benefit_acne": 0.55, "benefit_oil_control": 0.25, "benefit_barrier": 0.0},
    {"inci_name": "retinal", "synonyms": [], "category": "retinoid", "irritation_risk": 0.5, "acne_risk": 0.07, "benefit_acne": 0.5, "benefit_oil_control": 0.2, "benefit_barrier": 0.0},
    {"inci_name": "ascorbic acid", "synonyms": ["vitamin c"], "category": "antioxidant", "irritation_risk": 0.3, "acne_risk": 0.03, "benefit_acne": 0.15, "benefit_oil_control": 0.1, "benefit_barrier": 0.15},
    {"inci_name": "fragrance", "synonyms": ["parfum", "perfume"], "category": "fragrance", "irritation_risk": 0.45, "acne_risk": 0.08, "benefit_acne": 0.0, "benefit_oil_control": 0.0, "benefit_barrier": 0.0},
    {"inci_name": "alcohol denat", "synonyms": ["alcohol denat."], "category": "solvent", "irritation_risk": 0.5, "acne_risk": 0.05, "benefit_acne": 0.0, "benefit_oil_control": 0.15, "benefit_barrier": 0.0},
    {"inci_name": "glycerin", "synonyms": [], "category": "humectant", "irritation_risk": 0.01, "acne_risk": 0.01, "benefit_acne": 0.0, "benefit_oil_control": 0.0, "benefit_barrier": 0.7},
    {"inci_name": "hyaluronic acid", "synonyms": [], "category": "humectant", "irritation_risk": 0.01, "acne_risk": 0.01, "benefit_acne": 0.0, "benefit_oil_control": 0.0, "benefit_barrier": 0.55},
    {"inci_name": "ceramide", "synonyms": [], "category": "barrier", "irritation_risk": 0.01, "acne_risk": 0.01, "benefit_acne": 0.0, "benefit_oil_control": 0.0, "benefit_barrier": 0.9},
    {"inci_name": "panthenol", "synonyms": [], "category": "soothing", "irritation_risk": 0.01, "acne_risk": 0.01, "benefit_acne": 0.05, "benefit_oil_control": 0.0, "benefit_barrier": 0.65},
    {"inci_name": "azelaic acid", "synonyms": [], "category": "active", "irritation_risk": 0.25, "acne_risk": 0.02, "benefit_acne": 0.7, "benefit_oil_control": 0.35, "benefit_barrier": 0.05},
    {"inci_name": "benzoyl peroxide", "synonyms": [], "category": "active", "irritation_risk": 0.6, "acne_risk": 0.02, "benefit_acne": 0.8, "benefit_oil_control": 0.25, "benefit_barrier": 0.0},
    {"inci_name": "zinc pca", "synonyms": [], "category": "oil control", "irritation_risk": 0.04, "acne_risk": 0.01, "benefit_acne": 0.35, "benefit_oil_control": 0.75, "benefit_barrier": 0.05},
    {"inci_name": "tocopherol", "synonyms": [], "category": "antioxidant", "irritation_risk": 0.05, "acne_risk": 0.15, "benefit_acne": 0.0, "benefit_oil_control": 0.0, "benefit_barrier": 0.25},
    {"inci_name": "mineral oil", "synonyms": [], "category": "emollient", "irritation_risk": 0.01, "acne_risk": 0.12, "benefit_acne": 0.0, "benefit_oil_control": 0.0, "benefit_barrier": 0.45},
    {"inci_name": "shea butter", "synonyms": [], "category": "emollient", "irritation_risk": 0.03, "acne_risk": 0.35, "benefit_acne": 0.0, "benefit_oil_control": 0.0, "benefit_barrier": 0.5},
]


def seed_ingredients(db: Session) -> None:
    existing = set(db.scalars(select(Ingredient.inci_name)).all())
    for payload in SEED_INGREDIENTS:
        if payload["inci_name"] not in existing:
            db.add(Ingredient(**payload))
    db.commit()
