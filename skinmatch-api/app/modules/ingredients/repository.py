from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.ingredients.models import Ingredient


def list_ingredients(db: Session) -> list[Ingredient]:
    return list(db.scalars(select(Ingredient).order_by(Ingredient.inci_name)).all())
