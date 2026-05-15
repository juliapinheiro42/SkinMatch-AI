from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.modules.skin_profiles.schemas import SkinProfileInput


class AnalysisRequest(BaseModel):
    ingredient_list: str | None = None
    raw_ingredient_list: str | None = None
    skin_profile: SkinProfileInput
    main_goal: str = "general"
    product_name: str | None = None
    brand: str | None = None

    @model_validator(mode="after")
    def require_formula(self) -> "AnalysisRequest":
        if not self.formula_text:
            raise ValueError("ingredient_list or raw_ingredient_list is required")
        return self

    @property
    def formula_text(self) -> str:
        return (self.raw_ingredient_list or self.ingredient_list or "").strip()


class ParsedIngredient(BaseModel):
    position: int
    raw_name: str
    normalized_name: str
    inci_name: str
    unknown: bool
    concentration_band: str


class AnalysisResponse(BaseModel):
    analysis_id: UUID
    product_id: UUID
    compatibility_score: int
    verdict: str
    irritation_risk: float
    acne_risk: float
    benefit_score: float
    barrier_support: float
    applied_rules: list[str]
    positive_ingredients: list[str]
    warning_ingredients: list[str]
    unknown_ingredients: list[str]
    parsed_ingredients: list[ParsedIngredient]
    recommendation: str
    disclaimer: str


class AnalysisHistoryItem(BaseModel):
    analysis_id: UUID
    product_id: UUID | None = None
    product_name: str | None
    brand: str | None
    main_goal: str
    compatibility_score: float
    verdict: str
    irritation_risk: float
    acne_risk: float
    benefit_score: float
    created_at: datetime


class ProductFeedbackRequest(BaseModel):
    used_product: bool
    usage_days: int | None = Field(default=None, ge=0)
    usage_frequency: str | None = None
    irritation_level: int = Field(ge=0, le=5)
    acne_level: int = Field(ge=0, le=5)
    dryness_level: int = Field(ge=0, le=5)
    satisfaction_level: int = Field(ge=0, le=5)
    noticed_benefits: list[str] = Field(default_factory=list)
    would_buy_again: bool | None = None
    comments: str | None = None

    @model_validator(mode="after")
    def require_usage_days_when_used(self) -> "ProductFeedbackRequest":
        if self.used_product and self.usage_days is None:
            raise ValueError("usage_days is required when used_product is true")
        return self


class ProductFeedbackResponse(ProductFeedbackRequest):
    id: UUID
    user_id: UUID
    analysis_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class AnalysisDetail(BaseModel):
    analysis_id: UUID
    product_id: UUID | None
    product_name: str | None
    brand: str | None
    main_goal: str
    raw_ingredient_list: str
    skin_profile_snapshot: dict[str, Any]
    parsed_formula_snapshot: list[dict[str, Any]]
    compatibility_score: float
    verdict: str
    irritation_risk: float
    acne_risk: float
    benefit_score: float
    barrier_support: float
    applied_rules: list[str]
    positive_ingredients: list[str]
    warning_ingredients: list[str]
    unknown_ingredients: list[str]
    recommendation: str
    disclaimer: str
    created_at: datetime
    feedback: ProductFeedbackResponse | None = None


class CommonTrigger(BaseModel):
    ingredient: str
    reaction: str
    occurrences: int


class WellToleratedIngredient(BaseModel):
    ingredient: str
    positive_feedbacks: int


class IngredientAffinityInsight(BaseModel):
    ingredient_name: str
    tolerance_score: float
    confidence: float
    feedback_count: int
    confidence_label: str


class PersonalInsightsResponse(BaseModel):
    total_feedbacks: int
    common_triggers: list[CommonTrigger]
    well_tolerated_ingredients: list[WellToleratedIngredient]
    patterns: list[str]
    ingredient_affinity: dict[str, list[IngredientAffinityInsight]] = Field(
        default_factory=lambda: {"problematic": [], "well_tolerated": [], "low_confidence": []}
    )
