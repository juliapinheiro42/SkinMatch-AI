from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.agent.schemas import AgentChatRequest, AgentChatResponse
from app.modules.agent.service import chat


router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat", response_model=AgentChatResponse)
def agent_chat(request: AgentChatRequest, db: Session = Depends(get_db)) -> AgentChatResponse:
    return chat(db, request)
