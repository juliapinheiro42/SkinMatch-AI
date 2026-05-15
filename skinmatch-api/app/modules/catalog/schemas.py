from uuid import UUID

from pydantic import BaseModel, Field


class CatalogImportResult(BaseModel):
    imported: int
    reused: int
    skipped: int


class CatalogProductResponse(BaseModel):
    product_id: UUID
    name: str
    brand: str
    category: str | None
    routine_step: str | None
    usage_periods: list[str]
    price_range: str | None
    tags: list[str]
    is_active_treatment: bool
    is_sunscreen: bool
    is_moisturizer: bool
    is_cleanser: bool
    source: str | None
    source_url: str | None
    catalog_status: str


class CatalogFilters(BaseModel):
    category: str | None = None
    routine_step: str | None = None
    tag: str | None = None
    price_range: str | None = None
    is_active_treatment: bool | None = None
    limit: int = Field(default=100, ge=1, le=500)
