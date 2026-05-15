import math
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.formulas.service import formula_hash, normalize_formula_text, product_normalized_name
from app.modules.products.embedding_service import generate_formula_embedding
from app.modules.products.embedding_service import _deterministic_embedding
from app.config import settings
from app.modules.products.models import Product
from app.modules.products.repository import (
    create_product,
    get_product,
    get_product_by_hash,
    list_products_with_embeddings,
    update_product_embedding,
    update_product_catalog_fields,
)


def get_or_create_product_for_formula(
    db: Session,
    raw_ingredient_list: str,
    parsed_formula_snapshot: list[dict],
    product_name: str | None = None,
    brand: str | None = None,
    catalog_fields: dict | None = None,
    generate_external_embedding: bool = True,
) -> Product:
    hash_value = formula_hash(raw_ingredient_list)
    existing = get_product_by_hash(db, hash_value)
    if existing:
        if existing.embedding is None:
            embedding = (
                generate_formula_embedding(raw_ingredient_list)
                if generate_external_embedding
                else _deterministic_embedding(normalize_formula_text(raw_ingredient_list), settings.embedding_dimensions)
            )
            update_product_embedding(db, existing, embedding)
        if catalog_fields:
            existing = update_product_catalog_fields(db, existing, **catalog_fields)
        return existing

    name = product_name or "Produto sem nome"
    product_brand = brand or "Unknown"
    return create_product(
        db,
        name=name,
        brand=product_brand,
        normalized_name=product_normalized_name(name, product_brand),
        formula_hash=hash_value,
        raw_ingredient_list=normalize_formula_text(raw_ingredient_list),
        parsed_formula_snapshot=parsed_formula_snapshot,
        embedding=(
            generate_formula_embedding(raw_ingredient_list)
            if generate_external_embedding
            else _deterministic_embedding(normalize_formula_text(raw_ingredient_list), settings.embedding_dimensions)
        ),
        **(catalog_fields or {}),
    )


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left)) or 1.0
    right_norm = math.sqrt(sum(b * b for b in right)) or 1.0
    return dot / (left_norm * right_norm)


def similar_products(db: Session, product_id: UUID, limit: int = 5) -> list[dict]:
    product = get_product(db, product_id)
    if product is None:
        return []
    if not product.raw_ingredient_list:
        return []
    if product.embedding is None:
        product = update_product_embedding(db, product, generate_formula_embedding(product.raw_ingredient_list))

    candidates = list_products_with_embeddings(db, exclude_product_id=product_id)
    scored = [
        {
            "product_id": candidate.id,
            "name": candidate.name,
            "brand": candidate.brand,
            "similarity": round(max(0.0, min(1.0, _cosine_similarity(product.embedding, candidate.embedding))), 3),
        }
        for candidate in candidates
        if candidate.embedding is not None
    ]
    return sorted(scored, key=lambda item: item["similarity"], reverse=True)[:limit]
