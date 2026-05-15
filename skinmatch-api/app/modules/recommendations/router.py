from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.recommendations.schemas import RecommendationItem, RecommendationRequest
from app.modules.recommendations.service import recommend_products


router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("", response_model=list[RecommendationItem])
def recommendations(request: RecommendationRequest, db: Session = Depends(get_db)) -> list[RecommendationItem]:
    return recommend_products(db, request)
