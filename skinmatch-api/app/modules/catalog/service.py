import csv
from io import StringIO
from typing import Any

from sqlalchemy.orm import Session

from app.modules.analysis.parser import parse_formula
from app.modules.formulas.service import normalize_formula_text
from app.modules.ingredients.repository import list_ingredients
from app.modules.products.models import Product
from app.modules.products.product_service import get_or_create_product_for_formula
from app.modules.products.repository import get_product_by_hash, list_catalog_products
from app.modules.catalog.schemas import CatalogImportResult, CatalogProductResponse
from app.modules.formulas.service import formula_hash


REQUIRED_COLUMNS = {
    "name",
    "brand",
    "category",
    "routine_step",
    "usage_periods",
    "price_range",
    "raw_ingredient_list",
    "tags",
    "source",
}


def split_values(value: str | None) -> list[str]:
    if not value:
        return []
    normalized = value.replace("|", ";")
    return [item.strip().lower() for item in normalized.split(";") if item.strip()]


def infer_catalog_flags(category: str | None, routine_step: str | None, tags: list[str]) -> dict[str, bool]:
    values = {str(category or "").lower(), str(routine_step or "").lower(), *tags}
    return {
        "is_active_treatment": bool(values & {"treatment", "active", "acne", "acne_treatment", "barrier_repair"}),
        "is_sunscreen": bool(values & {"sunscreen", "spf"}),
        "is_moisturizer": bool(values & {"moisturizer", "barrier", "barrier_repair"}),
        "is_cleanser": bool(values & {"cleanser"}),
    }


def parsed_snapshot(parsed: list[dict]) -> list[dict]:
    return [{key: value for key, value in item.items() if key != "ingredient"} for item in parsed]


def catalog_fields(row: dict[str, str]) -> dict[str, Any]:
    category = (row.get("category") or "").strip().lower() or None
    routine_step = (row.get("routine_step") or "").strip().lower() or None
    tags = split_values(row.get("tags"))
    return {
        "category": category,
        "routine_step": routine_step,
        "usage_periods": split_values(row.get("usage_periods")),
        "price_range": (row.get("price_range") or "").strip().lower() or None,
        "tags": tags,
        "source": (row.get("source") or "").strip() or None,
        "source_url": (row.get("source_url") or "").strip() or None,
        "catalog_status": "active",
        **infer_catalog_flags(category, routine_step, tags),
    }


def import_catalog_csv(db: Session, csv_text: str, *, generate_external_embeddings: bool = True) -> CatalogImportResult:
    reader = csv.DictReader(StringIO(csv_text))
    if not reader.fieldnames or not REQUIRED_COLUMNS.issubset(set(reader.fieldnames)):
        missing = sorted(REQUIRED_COLUMNS - set(reader.fieldnames or []))
        raise ValueError(f"CSV missing required columns: {', '.join(missing)}")

    ingredients = list_ingredients(db)
    imported = 0
    reused = 0
    skipped = 0

    for row in reader:
        raw_formula = (row.get("raw_ingredient_list") or "").strip()
        name = (row.get("name") or "").strip()
        brand = (row.get("brand") or "").strip()
        if not raw_formula or not name or not brand:
            skipped += 1
            continue

        normalized_formula = normalize_formula_text(raw_formula)
        existed = get_product_by_hash(db, formula_hash(normalized_formula)) is not None
        parsed = parse_formula(normalized_formula, ingredients)
        get_or_create_product_for_formula(
            db,
            raw_ingredient_list=normalized_formula,
            parsed_formula_snapshot=parsed_snapshot(parsed),
            product_name=name,
            brand=brand,
            catalog_fields=catalog_fields(row),
            generate_external_embedding=generate_external_embeddings,
        )
        if existed:
            reused += 1
        else:
            imported += 1

    return CatalogImportResult(imported=imported, reused=reused, skipped=skipped)


def product_response(product: Product) -> CatalogProductResponse:
    return CatalogProductResponse(
        product_id=product.id,
        name=product.name,
        brand=product.brand,
        category=product.category,
        routine_step=product.routine_step,
        usage_periods=product.usage_periods or [],
        price_range=product.price_range,
        tags=product.tags or [],
        is_active_treatment=product.is_active_treatment,
        is_sunscreen=product.is_sunscreen,
        is_moisturizer=product.is_moisturizer,
        is_cleanser=product.is_cleanser,
        source=getattr(product, "source", None),
        source_url=getattr(product, "source_url", None),
        catalog_status=getattr(product, "catalog_status", "active"),
    )


def list_catalog(
    db: Session,
    *,
    category: str | None = None,
    routine_step: str | None = None,
    tag: str | None = None,
    price_range: str | None = None,
    is_active_treatment: bool | None = None,
    limit: int = 100,
) -> list[CatalogProductResponse]:
    products = list_catalog_products(
        db,
        category=category,
        routine_step=routine_step,
        tag=tag,
        price_range=price_range,
        is_active_treatment=is_active_treatment,
        limit=limit,
    )
    return [product_response(product) for product in products]
