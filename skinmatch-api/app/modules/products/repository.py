from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.modules.products.models import Product, ProductFormula


def get_product_by_hash(db: Session, formula_hash: str) -> Product | None:
    return db.scalar(select(Product).where(Product.formula_hash == formula_hash))


def get_product(db: Session, product_id: UUID) -> Product | None:
    return db.scalar(select(Product).options(joinedload(Product.formulas)).where(Product.id == product_id))


def list_products_with_embeddings(db: Session, exclude_product_id: UUID | None = None) -> list[Product]:
    statement = select(Product).where(Product.embedding.is_not(None))
    if exclude_product_id:
        statement = statement.where(Product.id != exclude_product_id)
    return list(db.scalars(statement).all())


def list_products_with_formulas(db: Session, limit: int = 100) -> list[Product]:
    statement = (
        select(Product)
        .options(joinedload(Product.formulas))
        .where(Product.raw_ingredient_list.is_not(None), Product.catalog_status == "active")
        .limit(limit)
    )
    return list(db.scalars(statement).unique().all())


def list_catalog_products(
    db: Session,
    *,
    category: str | None = None,
    routine_step: str | None = None,
    tag: str | None = None,
    price_range: str | None = None,
    is_active_treatment: bool | None = None,
    limit: int = 100,
) -> list[Product]:
    statement = select(Product).options(joinedload(Product.formulas)).where(Product.catalog_status == "active")
    if category:
        statement = statement.where(Product.category == category)
    if routine_step:
        statement = statement.where(Product.routine_step == routine_step)
    if price_range:
        statement = statement.where(Product.price_range == price_range)
    if is_active_treatment is not None:
        statement = statement.where(Product.is_active_treatment == is_active_treatment)
    if tag:
        statement = statement.where(Product.tags.contains([tag]))
    statement = statement.order_by(Product.name).limit(limit)
    return list(db.scalars(statement).unique().all())


def create_product(
    db: Session,
    name: str,
    brand: str,
    normalized_name: str,
    formula_hash: str,
    raw_ingredient_list: str,
    parsed_formula_snapshot: list[dict],
    embedding: list[float] | None,
    category: str | None = None,
    routine_step: str | None = None,
    usage_periods: list[str] | None = None,
    price_range: str | None = None,
    tags: list[str] | None = None,
    is_active_treatment: bool = False,
    is_sunscreen: bool = False,
    is_moisturizer: bool = False,
    is_cleanser: bool = False,
    source: str | None = None,
    source_url: str | None = None,
    catalog_status: str = "active",
) -> Product:
    product = Product(
        name=name,
        brand=brand,
        normalized_name=normalized_name,
        formula_hash=formula_hash,
        raw_ingredient_list=raw_ingredient_list,
        embedding=embedding,
        category=category,
        routine_step=routine_step,
        usage_periods=usage_periods or [],
        price_range=price_range,
        tags=tags or [],
        is_active_treatment=is_active_treatment,
        is_sunscreen=is_sunscreen,
        is_moisturizer=is_moisturizer,
        is_cleanser=is_cleanser,
        source=source,
        source_url=source_url,
        catalog_status=catalog_status,
    )
    product.formulas.append(ProductFormula(parsed_formula_snapshot=parsed_formula_snapshot))
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product_catalog_fields(db: Session, product: Product, **fields) -> Product:
    for key, value in fields.items():
        if value is not None and hasattr(product, key):
            setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


def update_product_embedding(db: Session, product: Product, embedding: list[float]) -> Product:
    product.embedding = embedding
    db.commit()
    db.refresh(product)
    return product
