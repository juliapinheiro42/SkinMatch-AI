from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.analysis.schemas import PersonalInsightsResponse
from app.modules.insights.service import get_personal_insights


TEMP_USER_ID = UUID("00000000-0000-0000-0000-000000000001")

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/personal", response_model=PersonalInsightsResponse)
def personal_insights(db: Session = Depends(get_db)) -> PersonalInsightsResponse:
    return get_personal_insights(db, TEMP_USER_ID)
