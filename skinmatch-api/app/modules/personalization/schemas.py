from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class IngredientAffinityItem(BaseModel):
    id: UUID
    user_id: UUID
    ingredient_name: str
    tolerance_score: float
    irritation_count: int
    acne_count: int
    positive_count: int
    neutral_count: int
    confidence: float
    last_seen_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IngredientAffinitySummary(BaseModel):
    ingredient_name: str
    tolerance_score: float
    confidence: float
    feedback_count: int
    confidence_label: str
