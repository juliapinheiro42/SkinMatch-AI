from uuid import UUID

from pydantic import BaseModel


class SimilarProduct(BaseModel):
    product_id: UUID
    name: str
    brand: str
    similarity: float


class CatalogProduct(BaseModel):
    product_id: UUID
    name: str
    brand: str
    category: str | None = None
    routine_step: str | None = None
    usage_periods: list[str] = []
    price_range: str | None = None
    tags: list[str] = []
    is_active_treatment: bool = False
    is_sunscreen: bool = False
    is_moisturizer: bool = False
    is_cleanser: bool = False
    source: str | None = None
    source_url: str | None = None
    catalog_status: str
