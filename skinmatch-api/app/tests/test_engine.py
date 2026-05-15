from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.modules.analysis.engine import analyze_formula
from app.modules.analysis import router as analysis_router
from app.modules.formulas.ocr_service import clean_ingredient_text
from app.modules.formulas.service import formula_hash
from app.modules.insights import service as insights_service
from app.modules.products.embedding_service import generate_formula_embedding
from app.modules.products.product_service import get_or_create_product_for_formula, similar_products
from app.modules.skin_profiles.schemas import SkinProfileInput


def ingredient(
    inci_name: str,
    irritation_risk: float = 0.0,
    acne_risk: float = 0.0,
    benefit_acne: float = 0.0,
    benefit_oil_control: float = 0.0,
    benefit_barrier: float = 0.0,
) -> SimpleNamespace:
    return SimpleNamespace(
        inci_name=inci_name,
        synonyms=[],
        irritation_risk=irritation_risk,
        acne_risk=acne_risk,
        benefit_acne=benefit_acne,
        benefit_oil_control=benefit_oil_control,
        benefit_barrier=benefit_barrier,
    )


def parsed(item: SimpleNamespace, position: int = 1, band: str = "high") -> dict:
    return {
        "position": position,
        "raw_name": item.inci_name,
        "normalized_name": item.inci_name,
        "inci_name": item.inci_name,
        "unknown": False,
        "concentration_band": band,
        "ingredient": item,
    }


def test_rule_001_fragrance_sensitive() -> None:
    result = analyze_formula(
        [parsed(ingredient("fragrance", irritation_risk=0.45))],
        SkinProfileInput(skin_type="dry", sensitive_skin=True, acne_prone=False, barrier_compromised=False),
    )

    assert "RULE_001" in result["applied_rules"]
    assert "fragrance" in result["warning_ingredients"]


def test_rule_002_alcohol_denat_barrier() -> None:
    result = analyze_formula(
        [parsed(ingredient("alcohol denat", irritation_risk=0.5))],
        SkinProfileInput(skin_type="dry", sensitive_skin=False, acne_prone=False, barrier_compromised=True),
    )

    assert "RULE_002" in result["applied_rules"]
    assert result["irritation_risk"] >= 0.85


def test_rule_003_salicylic_acid_acne() -> None:
    result = analyze_formula(
        [parsed(ingredient("salicylic acid", irritation_risk=0.35, benefit_acne=0.85, benefit_oil_control=0.7))],
        SkinProfileInput(skin_type="oily", sensitive_skin=False, acne_prone=True, barrier_compromised=False),
    )

    assert "RULE_003" in result["applied_rules"]
    assert "salicylic acid" in result["positive_ingredients"]


def test_tolerated_ingredient_reduces_risk() -> None:
    retinol = ingredient("retinol", irritation_risk=0.6, acne_risk=0.1)
    profile = SkinProfileInput(
        skin_type="normal",
        sensitive_skin=False,
        acne_prone=False,
        barrier_compromised=False,
        tolerated_ingredients=["retinol"],
    )

    tolerated = analyze_formula([parsed(retinol)], profile)
    not_tolerated = analyze_formula(
        [parsed(retinol)],
        SkinProfileInput(skin_type="normal", sensitive_skin=False, acne_prone=False, barrier_compromised=False),
    )

    assert "RULE_006" in tolerated["applied_rules"]
    assert tolerated["irritation_risk"] < not_tolerated["irritation_risk"]


def test_engine_applies_rule_008_for_common_trigger() -> None:
    fragrance = ingredient("fragrance", irritation_risk=0.1)
    result = analyze_formula(
        [parsed(fragrance)],
        SkinProfileInput(skin_type="normal", sensitive_skin=False, acne_prone=False, barrier_compromised=False),
        personal_insights={"common_triggers": {"fragrance"}, "well_tolerated_ingredients": set()},
    )

    assert "RULE_008" in result["applied_rules"]
    assert "fragrance" in result["warning_ingredients"]


def test_engine_applies_rule_009_for_well_tolerated() -> None:
    niacinamide = ingredient("niacinamide", irritation_risk=0.2, benefit_acne=0.2)
    result = analyze_formula(
        [parsed(niacinamide)],
        SkinProfileInput(skin_type="normal", sensitive_skin=False, acne_prone=False, barrier_compromised=False),
        personal_insights={"common_triggers": set(), "well_tolerated_ingredients": {"niacinamide"}},
    )

    assert "RULE_009" in result["applied_rules"]
    assert "niacinamide" in result["positive_ingredients"]


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analysis_endpoint(monkeypatch) -> None:
    ingredients = [
        ingredient("glycerin", benefit_barrier=0.7),
        ingredient("niacinamide", benefit_acne=0.45, benefit_oil_control=0.55, benefit_barrier=0.35),
        ingredient("fragrance", irritation_risk=0.45),
    ]

    monkeypatch.setattr(analysis_router, "list_ingredients", lambda db: ingredients)
    monkeypatch.setattr(
        analysis_router,
        "insights_for_engine",
        lambda db, user_id: {"common_triggers": set(), "well_tolerated_ingredients": set()},
    )
    monkeypatch.setattr(
        analysis_router,
        "create_analysis_record",
        lambda db, record: SimpleNamespace(
            id=UUID("11111111-1111-1111-1111-111111111111"),
            product_id=UUID("22222222-2222-2222-2222-222222222222"),
        ),
    )
    monkeypatch.setattr(
        analysis_router,
        "get_or_create_product_for_formula",
        lambda db, **kwargs: SimpleNamespace(id=UUID("22222222-2222-2222-2222-222222222222")),
    )
    monkeypatch.setattr(
        analysis_router,
        "get_or_create_formula_cache",
        lambda db, formula_hash, parsed: SimpleNamespace(
            base_irritation_risk=0.0,
            base_acne_risk=0.0,
            base_benefit_score=0.0,
            base_barrier_support=0.0,
        ),
    )

    client = TestClient(app)
    response = client.post(
        "/analysis",
        json={
            "ingredient_list": "Glycerin, Niacinamide, Fragrance",
            "skin_profile": {
                "skin_type": "oily",
                "sensitive_skin": True,
                "acne_prone": True,
                "barrier_compromised": False,
                "known_triggers": [],
                "tolerated_ingredients": [],
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["analysis_id"] == "11111111-1111-1111-1111-111111111111"
    assert body["product_id"] == "22222222-2222-2222-2222-222222222222"
    assert "compatibility_score" in body
    assert "RULE_001" in body["applied_rules"]


def test_analysis_history_returns_saved_records(monkeypatch) -> None:
    analysis_id = uuid4()
    monkeypatch.setattr(
        analysis_router,
        "list_analysis_records",
        lambda db, **kwargs: [
            SimpleNamespace(
                id=analysis_id,
                product_id=uuid4(),
                product_name="Serum Antiacne X",
                brand="Marca Y",
                main_goal="acne",
                compatibility_score=58,
                verdict="caution",
                irritation_risk=0.74,
                acne_risk=0.32,
                benefit_score=0.68,
                created_at=datetime(2026, 5, 3, tzinfo=timezone.utc),
            )
        ],
    )

    client = TestClient(app)
    response = client.get("/analysis/history")

    assert response.status_code == 200
    body = response.json()
    assert body[0]["analysis_id"] == str(analysis_id)
    assert body[0]["product_name"] == "Serum Antiacne X"


def test_analysis_detail_returns_full_record(monkeypatch) -> None:
    analysis_id = uuid4()
    record = SimpleNamespace(
        id=analysis_id,
        product_id=uuid4(),
        product_name="Serum",
        brand="Marca",
        main_goal="acne",
        raw_ingredient_list="Aqua, Fragrance",
        skin_profile_snapshot={"skin_type": "oily"},
        parsed_formula_snapshot=[{"inci_name": "fragrance", "unknown": False}],
        compatibility_score=58,
        verdict="caution",
        irritation_risk=0.7,
        acne_risk=0.2,
        benefit_score=0.5,
        barrier_support=0.1,
        applied_rules=["RULE_001"],
        positive_ingredients=[],
        warning_ingredients=["fragrance"],
        unknown_ingredients=[],
        recommendation="Patch test.",
        disclaimer="Educational.",
        created_at=datetime(2026, 5, 3, tzinfo=timezone.utc),
        feedback=None,
    )
    monkeypatch.setattr(analysis_router, "get_analysis_record", lambda db, user_id, analysis_id: record)

    client = TestClient(app)
    response = client.get(f"/analysis/{analysis_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["analysis_id"] == str(analysis_id)
    assert body["raw_ingredient_list"] == "Aqua, Fragrance"
    assert body["applied_rules"] == ["RULE_001"]


def test_feedback_endpoint_creates_feedback(monkeypatch) -> None:
    analysis_id = uuid4()
    saved = SimpleNamespace(
        id=uuid4(),
        user_id=analysis_router.TEMP_USER_ID,
        analysis_id=analysis_id,
        used_product=True,
        usage_days=14,
        usage_frequency="3x_per_week",
        irritation_level=3,
        acne_level=1,
        dryness_level=2,
        satisfaction_level=4,
        noticed_benefits=["less_oiliness"],
        would_buy_again=True,
        comments="Funcionou.",
        created_at=datetime(2026, 5, 3, tzinfo=timezone.utc),
    )

    monkeypatch.setattr(analysis_router, "get_analysis_record", lambda db, user_id, analysis_id: SimpleNamespace())
    monkeypatch.setattr(analysis_router, "upsert_feedback", lambda db, **kwargs: saved)

    client = TestClient(app)
    response = client.post(
        f"/analysis/{analysis_id}/feedback",
        json={
            "used_product": True,
            "usage_days": 14,
            "usage_frequency": "3x_per_week",
            "irritation_level": 3,
            "acne_level": 1,
            "dryness_level": 2,
            "satisfaction_level": 4,
            "noticed_benefits": ["less_oiliness"],
            "would_buy_again": True,
            "comments": "Funcionou.",
        },
    )

    assert response.status_code == 200
    assert response.json()["irritation_level"] == 3


def test_feedback_endpoint_updates_existing_feedback(monkeypatch) -> None:
    analysis_id = uuid4()
    calls = []

    def fake_upsert(db, **kwargs):
        calls.append(kwargs["payload"])
        return SimpleNamespace(
            id=uuid4(),
            user_id=analysis_router.TEMP_USER_ID,
            analysis_id=analysis_id,
            used_product=True,
            usage_days=21,
            usage_frequency="daily",
            irritation_level=1,
            acne_level=0,
            dryness_level=1,
            satisfaction_level=5,
            noticed_benefits=["less_acne"],
            would_buy_again=True,
            comments="Melhorou.",
            created_at=datetime(2026, 5, 3, tzinfo=timezone.utc),
        )

    monkeypatch.setattr(analysis_router, "get_analysis_record", lambda db, user_id, analysis_id: SimpleNamespace())
    monkeypatch.setattr(analysis_router, "upsert_feedback", fake_upsert)

    client = TestClient(app)
    response = client.post(
        f"/analysis/{analysis_id}/feedback",
        json={
            "used_product": True,
            "usage_days": 21,
            "usage_frequency": "daily",
            "irritation_level": 1,
            "acne_level": 0,
            "dryness_level": 1,
            "satisfaction_level": 5,
            "noticed_benefits": ["less_acne"],
            "would_buy_again": True,
            "comments": "Melhorou.",
        },
    )

    assert response.status_code == 200
    assert calls[0]["satisfaction_level"] == 5


def test_personal_insights_identifies_fragrance_trigger(monkeypatch) -> None:
    monkeypatch.setattr(
        insights_service,
        "list_records_with_feedback",
        lambda db, user_id: [
            SimpleNamespace(
                parsed_formula_snapshot=[{"inci_name": "fragrance"}, {"inci_name": "niacinamide"}],
                feedback=SimpleNamespace(irritation_level=3, satisfaction_level=2),
            )
        ],
    )

    insights = insights_service.get_personal_insights(db=SimpleNamespace(), user_id=analysis_router.TEMP_USER_ID)

    assert insights.total_feedbacks == 1
    assert insights.common_triggers[0].ingredient == "fragrance"


def test_formula_hash_is_consistent() -> None:
    first = formula_hash("Aqua, Glycerin, Niacinamide")
    second = formula_hash(" aqua , glycerin , niacinamide. ")

    assert first == second


def test_product_service_does_not_duplicate_products() -> None:
    db = SimpleNamespace(products={})

    def fake_get_by_hash(db, hash_value):
        return db.products.get(hash_value)

    def fake_create_product(db, **payload):
        product = SimpleNamespace(id=uuid4(), **payload)
        db.products[payload["formula_hash"]] = product
        return product

    from app.modules.products import product_service

    original_get = product_service.get_product_by_hash
    original_create = product_service.create_product
    try:
        product_service.get_product_by_hash = fake_get_by_hash
        product_service.create_product = fake_create_product
        first = get_or_create_product_for_formula(db, "Aqua, Glycerin", [], "Serum", "Marca")
        second = get_or_create_product_for_formula(db, " aqua, glycerin. ", [], "Outro", "Marca")
    finally:
        product_service.get_product_by_hash = original_get
        product_service.create_product = original_create

    assert first.id == second.id
    assert len(db.products) == 1


def test_cache_is_reused(monkeypatch) -> None:
    from app.modules.formula_cache import service as cache_service

    calls = {"created": 0}
    monkeypatch.setattr(cache_service, "get_formula_cache", lambda db, formula_hash: SimpleNamespace(id=uuid4()))

    def fake_create(*args, **kwargs):
        calls["created"] += 1

    monkeypatch.setattr(cache_service, "create_formula_cache", fake_create)

    cached = cache_service.get_or_create_formula_cache(SimpleNamespace(), "abc", [])

    assert cached.id
    assert calls["created"] == 0


def test_ocr_cleans_ingredient_section() -> None:
    cleaned = clean_ingredient_text("Modo de uso X INGREDIENTS: Aqua, Glycerin; Niacinamide. Warning: avoid eyes")

    assert cleaned == "Aqua, Glycerin, Niacinamide"


def test_embedding_is_generated_without_api_key() -> None:
    embedding = generate_formula_embedding("Aqua, Glycerin")

    assert len(embedding) == 1536
    assert any(value != 0 for value in embedding)


def test_similar_products_returns_results(monkeypatch) -> None:
    product_id = uuid4()
    candidate_id = uuid4()
    product = SimpleNamespace(id=product_id, raw_ingredient_list="Aqua", embedding=[1.0, 0.0])
    candidate = SimpleNamespace(id=candidate_id, name="Similar", brand="Marca", embedding=[0.9, 0.1])

    from app.modules.products import product_service

    monkeypatch.setattr(product_service, "get_product", lambda db, product_id: product)
    monkeypatch.setattr(product_service, "list_products_with_embeddings", lambda db, exclude_product_id: [candidate])

    results = similar_products(SimpleNamespace(), product_id)

    assert results[0]["product_id"] == candidate_id
    assert results[0]["similarity"] > 0.9
