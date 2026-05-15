from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.skin_profiles.schemas import SkinProfileInput


class RoutineConstraints(BaseModel):
    avoid_ingredients: list[str] = Field(default_factory=list)
    max_steps: int = Field(default=5, ge=2, le=8)


class RoutineRequest(BaseModel):
    skin_profile: SkinProfileInput
    main_goal: str
    constraints: RoutineConstraints = Field(default_factory=RoutineConstraints)


class RoutineProduct(BaseModel):
    id: UUID
    name: str
    brand: str


class RoutineStep(BaseModel):
    step: int
    type: str
    product: RoutineProduct
    instructions: str
    reason: str


class RoutineResponse(BaseModel):
    morning_routine: list[RoutineStep]
    night_routine: list[RoutineStep]
    warnings: list[str]
