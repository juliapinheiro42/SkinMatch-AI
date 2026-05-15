from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.personalization.models import UserIngredientAffinity


def get_affinity_by_ingredient(db: Session, user_id: UUID, ingredient_name: str) -> UserIngredientAffinity | None:
    return db.scalar(
        select(UserIngredientAffinity).where(
            UserIngredientAffinity.user_id == user_id,
            UserIngredientAffinity.ingredient_name == ingredient_name,
        )
    )


def upsert_affinity(db: Session, affinity: UserIngredientAffinity) -> UserIngredientAffinity:
    db.add(affinity)
    db.commit()
    db.refresh(affinity)
    return affinity


def list_user_affinity(db: Session, user_id: UUID) -> list[UserIngredientAffinity]:
    return list(
        db.scalars(
            select(UserIngredientAffinity)
            .where(UserIngredientAffinity.user_id == user_id)
            .order_by(UserIngredientAffinity.ingredient_name)
        ).all()
    )
