from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.analysis.engine import analyze_formula
from app.modules.analysis.parser import parse_formula
from app.modules.analysis.schemas import (
    AnalysisDetail,
    AnalysisHistoryItem,
    AnalysisRequest,
    AnalysisResponse,
    ProductFeedbackRequest,
    ProductFeedbackResponse,
)
from app.modules.analysis_records.models import AnalysisRecord
from app.modules.analysis_records.repository import (
    create_analysis_record,
    get_analysis_record,
    list_analysis_records,
)
from app.modules.feedback.repository import upsert_feedback
from app.modules.formula_cache.service import get_or_create_formula_cache
from app.modules.formulas.service import formula_hash, normalize_formula_text
from app.modules.ingredients.repository import list_ingredients
from app.modules.insights.service import insights_for_engine
from app.modules.personalization.service import update_affinity_from_feedback
from app.modules.products.product_service import get_or_create_product_for_formula


router = APIRouter(prefix="/analysis", tags=["analysis"])
TEMP_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _parsed_snapshot(parsed: list[dict]) -> list[dict]:
    return [{key: value for key, value in item.items() if key != "ingredient"} for item in parsed]


def _history_item(record: AnalysisRecord) -> AnalysisHistoryItem:
    return AnalysisHistoryItem(
        analysis_id=record.id,
        product_id=record.product_id,
        product_name=record.product_name,
        brand=record.brand,
        main_goal=record.main_goal,
        compatibility_score=record.compatibility_score,
        verdict=record.verdict,
        irritation_risk=round(record.irritation_risk * 100),
        acne_risk=round(record.acne_risk * 100),
        benefit_score=round(record.benefit_score * 100),
        created_at=record.created_at,
    )


def _detail(record: AnalysisRecord) -> AnalysisDetail:
    feedback = ProductFeedbackResponse.model_validate(record.feedback) if record.feedback else None
    return AnalysisDetail(
        analysis_id=record.id,
        product_id=record.product_id,
        product_name=record.product_name,
        brand=record.brand,
        main_goal=record.main_goal,
        raw_ingredient_list=record.raw_ingredient_list,
        skin_profile_snapshot=record.skin_profile_snapshot,
        parsed_formula_snapshot=record.parsed_formula_snapshot,
        compatibility_score=record.compatibility_score,
        verdict=record.verdict,
        irritation_risk=record.irritation_risk,
        acne_risk=record.acne_risk,
        benefit_score=record.benefit_score,
        barrier_support=record.barrier_support,
        applied_rules=record.applied_rules,
        positive_ingredients=record.positive_ingredients,
        warning_ingredients=record.warning_ingredients,
        unknown_ingredients=record.unknown_ingredients,
        recommendation=record.recommendation,
        disclaimer=record.disclaimer,
        created_at=record.created_at,
        feedback=feedback,
    )


@router.post("", response_model=AnalysisResponse)
def analyze(request: AnalysisRequest, db: Session = Depends(get_db)) -> dict:
    ingredients = list_ingredients(db)
    normalized_formula = normalize_formula_text(request.formula_text)
    parsed = parse_formula(normalized_formula, ingredients)
    parsed_snapshot = _parsed_snapshot(parsed)
    product = get_or_create_product_for_formula(
        db,
        raw_ingredient_list=normalized_formula,
        parsed_formula_snapshot=parsed_snapshot,
        product_name=request.product_name,
        brand=request.brand,
    )
    cache = get_or_create_formula_cache(db, formula_hash(normalized_formula), parsed)
    personal_insights = insights_for_engine(db, TEMP_USER_ID)
    result = analyze_formula(
        parsed,
        request.skin_profile,
        personal_insights=personal_insights,
        base_cache={
            "base_irritation_risk": cache.base_irritation_risk,
            "base_acne_risk": cache.base_acne_risk,
            "base_benefit_score": cache.base_benefit_score,
            "base_barrier_support": cache.base_barrier_support,
        },
    )

    record = create_analysis_record(
        db,
        AnalysisRecord(
            user_id=TEMP_USER_ID,
            product_id=product.id,
            product_name=request.product_name,
            brand=request.brand,
            main_goal=request.main_goal,
            raw_ingredient_list=normalized_formula,
            skin_profile_snapshot=request.skin_profile.model_dump(mode="json"),
            parsed_formula_snapshot=parsed_snapshot,
            compatibility_score=result["compatibility_score"],
            verdict=result["verdict"],
            irritation_risk=result["irritation_risk"],
            acne_risk=result["acne_risk"],
            benefit_score=result["benefit_score"],
            barrier_support=result["barrier_support"],
            applied_rules=result["applied_rules"],
            positive_ingredients=result["positive_ingredients"],
            warning_ingredients=result["warning_ingredients"],
            unknown_ingredients=result["unknown_ingredients"],
            recommendation=result["recommendation"],
            disclaimer=result["disclaimer"],
        ),
    )

    result["analysis_id"] = record.id
    result["product_id"] = product.id
    result["parsed_ingredients"] = parsed_snapshot
    return result


@router.get("/history", response_model=list[AnalysisHistoryItem])
def history(
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    verdict: str | None = Query(default=None, pattern="^(high_risk|caution|good_match)$"),
    main_goal: str | None = None,
) -> list[AnalysisHistoryItem]:
    records = list_analysis_records(
        db,
        user_id=TEMP_USER_ID,
        limit=limit,
        offset=offset,
        verdict=verdict,
        main_goal=main_goal,
    )
    return [_history_item(record) for record in records]


@router.get("/{analysis_id}", response_model=AnalysisDetail)
def detail(analysis_id: UUID, db: Session = Depends(get_db)) -> AnalysisDetail:
    record = get_analysis_record(db, TEMP_USER_ID, analysis_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return _detail(record)


@router.post("/{analysis_id}/feedback", response_model=ProductFeedbackResponse)
def save_feedback(
    analysis_id: UUID,
    request: ProductFeedbackRequest,
    db: Session = Depends(get_db),
) -> ProductFeedbackResponse:
    record = get_analysis_record(db, TEMP_USER_ID, analysis_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Analysis not found")

    feedback = upsert_feedback(
        db,
        user_id=TEMP_USER_ID,
        analysis_id=analysis_id,
        payload=request.model_dump(),
    )
    update_affinity_from_feedback(db, TEMP_USER_ID, analysis_id, feedback)
    return ProductFeedbackResponse.model_validate(feedback)
