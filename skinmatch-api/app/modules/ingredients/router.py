from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.ingredients.repository import list_ingredients
from app.modules.ingredients.schemas import IngredientRead


router = APIRouter(prefix="/ingredients", tags=["ingredients"])


@router.get("", response_model=list[IngredientRead])
def get_ingredients(db: Session = Depends(get_db)) -> list[IngredientRead]:
    return list_ingredients(db)
