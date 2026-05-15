from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.products.product_service import similar_products
from app.modules.products.repository import get_product
from app.modules.products.schemas import SimilarProduct


router = APIRouter(prefix="/products", tags=["products"])


@router.get("/{product_id}/similar", response_model=list[SimilarProduct])
def get_similar_products(product_id: UUID, db: Session = Depends(get_db)) -> list[dict]:
    if get_product(db, product_id) is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return similar_products(db, product_id)
