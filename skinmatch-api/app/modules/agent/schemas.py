from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.skin_profiles.schemas import SkinProfileInput


EDUCATIONAL_DISCLAIMER = (
    "Esta resposta e uma estimativa educacional e nao substitui orientacao medica ou dermatologica."
)


class AgentIntent(StrEnum):
    analyze_product = "analyze_product"
    recommend_products = "recommend_products"
    generate_routine = "generate_routine"
    explain_reaction = "explain_reaction"
    compare_products = "compare_products"
    adjust_routine = "adjust_routine"
    explain_ingredients = "explain_ingredients"
    get_personal_insights = "get_personal_insights"
    general_question = "general_question"
    general_skincare_question = "general_skincare_question"
    unknown = "unknown"


class AgentChatContext(BaseModel):
    product_name: str | None = None
    brand: str | None = None
    raw_ingredient_list: str | None = None
    skin_profile: SkinProfileInput | None = None
    main_goal: str | None = None
    exclude_ingredients: list[str] = Field(default_factory=list)


class AgentChatRequest(BaseModel):
    user_id: UUID = UUID("00000000-0000-0000-0000-000000000001")
    message: str
    context: AgentChatContext = Field(default_factory=AgentChatContext)


class AgentToolResult(BaseModel):
    name: str
    result: Any


class AgentChatResponse(BaseModel):
    answer: str
    intent: AgentIntent
    tools_used: list[str]
    structured_result: Any | None = None
    confidence: str = "medium"
    missing_info: list[str] = Field(default_factory=list)
    follow_up_suggestion: str | None = None
    context_status: str = "available"
    risk_level: str = "low"
    safety_disclaimer: str = EDUCATIONAL_DISCLAIMER


class AgentMessageRecord(BaseModel):
    id: UUID
    user_id: UUID
    role: str
    content: str
    intent: AgentIntent | None = None
    confidence: str | None = None
    tools_used: list[str] = Field(default_factory=list)
    structured_result: Any | None = None
    user_context_snapshot: Any | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
