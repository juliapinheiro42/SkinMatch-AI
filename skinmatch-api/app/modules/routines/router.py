from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.routines.schemas import RoutineRequest, RoutineResponse
from app.modules.routines.service import generate_routine


router = APIRouter(prefix="/routines", tags=["routines"])


@router.post("/generate", response_model=RoutineResponse)
def generate(request: RoutineRequest, db: Session = Depends(get_db)) -> RoutineResponse:
    return generate_routine(db, request)
