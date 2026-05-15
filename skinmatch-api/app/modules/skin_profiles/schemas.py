from enum import StrEnum

from pydantic import BaseModel, Field


class SkinType(StrEnum):
    oily = "oily"
    dry = "dry"
    combination = "combination"
    normal = "normal"


class SkinProfileInput(BaseModel):
    skin_type: SkinType
    sensitive_skin: bool = False
    acne_prone: bool = False
    barrier_compromised: bool = False
    known_triggers: list[str] = Field(default_factory=list)
    tolerated_ingredients: list[str] = Field(default_factory=list)
