from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.skin_profiles.schemas import SkinProfileInput


class RecommendationConstraints(BaseModel):
    price_range: str | None = Field(default=None, pattern="^(low|mid|high)$")
    preferred_category: str | None = Field(default=None, pattern="^(cleanser|moisturizer|sunscreen|treatment)$")
    routine_step_needed: str | None = None
    max_irritation_risk: int | None = Field(default=None, ge=0, le=100)
    avoid_active_treatments: bool = False
    explicit_tolerated_ingredients: list[str] = Field(default_factory=list)
    explicit_trigger_ingredients: list[str] = Field(default_factory=list)
    explicit_goals: list[str] = Field(default_factory=list)


class RecommendationRequest(BaseModel):
    skin_profile: SkinProfileInput
    main_goal: str
    exclude_ingredients: list[str] = Field(default_factory=list)
    constraints: RecommendationConstraints = Field(default_factory=RecommendationConstraints)
    limit: int = Field(default=5, ge=1, le=20)


class RecommendationItem(BaseModel):
    product_id: UUID
    name: str
    brand: str
    category: str | None = None
    compatibility_score: int
    irritation_risk: int
    acne_risk: int
    benefit_score: int
    final_score: int
    score_breakdown: dict[str, int]
    reason_codes: list[str]
    reason: str
    key_ingredients: list[str]
