from uuid import UUID

from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session, joinedload

from app.modules.analysis_records.models import AnalysisRecord


def create_analysis_record(db: Session, record: AnalysisRecord) -> AnalysisRecord:
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_analysis_record(db: Session, user_id: UUID, analysis_id: UUID) -> AnalysisRecord | None:
    statement = (
        select(AnalysisRecord)
        .options(joinedload(AnalysisRecord.feedback))
        .where(AnalysisRecord.user_id == user_id, AnalysisRecord.id == analysis_id)
    )
    return db.scalar(statement)


def list_analysis_records(
    db: Session,
    user_id: UUID,
    limit: int = 20,
    offset: int = 0,
    verdict: str | None = None,
    main_goal: str | None = None,
) -> list[AnalysisRecord]:
    statement: Select[tuple[AnalysisRecord]] = select(AnalysisRecord).where(AnalysisRecord.user_id == user_id)

    if verdict:
        statement = statement.where(AnalysisRecord.verdict == verdict)
    if main_goal:
        statement = statement.where(AnalysisRecord.main_goal == main_goal)

    statement = statement.order_by(desc(AnalysisRecord.created_at)).limit(limit).offset(offset)
    return list(db.scalars(statement).all())


def list_records_with_feedback(db: Session, user_id: UUID) -> list[AnalysisRecord]:
    statement = (
        select(AnalysisRecord)
        .options(joinedload(AnalysisRecord.feedback))
        .where(AnalysisRecord.user_id == user_id, AnalysisRecord.feedback.has())
        .order_by(desc(AnalysisRecord.created_at))
    )
    return list(db.scalars(statement).all())
