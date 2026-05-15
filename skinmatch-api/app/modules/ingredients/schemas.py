from pydantic import BaseModel, ConfigDict, Field


class IngredientRead(BaseModel):
    id: int
    inci_name: str
    synonyms: list[str]
    category: str
    irritation_risk: float = Field(ge=0, le=1)
    acne_risk: float = Field(ge=0, le=1)
    benefit_acne: float = Field(ge=0, le=1)
    benefit_oil_control: float = Field(ge=0, le=1)
    benefit_barrier: float = Field(ge=0, le=1)

    model_config = ConfigDict(from_attributes=True)
