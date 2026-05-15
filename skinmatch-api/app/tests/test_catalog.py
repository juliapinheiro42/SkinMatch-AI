from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.modules.catalog import router as catalog_router
from app.modules.catalog import service as catalog_service
from app.modules.recommendations import service as recommendation_service
from app.modules.routines.service import select_best_products_for_routine
from app.modules.skin_profiles.schemas import SkinProfileInput


CSV_TEXT = """name,brand,category,routine_step,usage_periods,price_range,raw_ingredient_list,tags,source
Gel Teste,Marca A,cleanser,cleanser,morning;night,mid,"Aqua, Glycerin, Decyl Glucoside",cleanser;gentle,test
"""


def product_snapshot(name: str) -> list[dict]:
    return [
        {
            "position": 1,
            "raw_name": name,
            "normalized_name": name,
            "inci_name": name,
            "unknown": False,
            "concentration_band": "high",
        }
    ]


def fake_product(name: str, raw: str | None, category: str = "cleanser") -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        name=name,
        brand="Marca",
        raw_ingredient_list=raw,
        category=category,
        routine_step=category if category != "acne_treatment" else "treatment",
        usage_periods=["morning"],
        price_range="mid",
        tags=[category],
        is_active_treatment=category == "acne_treatment",
        is_sunscreen=category == "sunscreen",
        is_moisturizer=category == "moisturizer",
        is_cleanser=category == "cleanser",
        formulas=[SimpleNamespace(parsed_formula_snapshot=product_snapshot("glycerin"))],
    )


def test_catalog_import_csv_endpoint(monkeypatch) -> None:
    monkeypatch.setattr(catalog_router, "import_catalog_csv", lambda db, text: SimpleNamespace(imported=1, reused=0, skipped=0))

    response = TestClient(app).post(
        "/catalog/import-csv",
        files={"file": ("catalog.csv", CSV_TEXT, "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["imported"] == 1


def test_catalog_import_does_not_duplicate_same_formula_hash(monkeypatch) -> None:
    seen: set[str] = set()

    monkeypatch.setattr(catalog_service, "list_ingredients", lambda db: [])
    monkeypatch.setattr(catalog_service, "parse_formula", lambda formula, ingredients: [])

    def fake_get_by_hash(db, hash_value):
        return SimpleNamespace(id=uuid4()) if hash_value in seen else None

    def fake_get_or_create(db, raw_ingredient_list, **kwargs):
        seen.add(catalog_service.formula_hash(raw_ingredient_list))
        return SimpleNamespace(id=uuid4())

    monkeypatch.setattr(catalog_service, "get_product_by_hash", fake_get_by_hash)
    monkeypatch.setattr(catalog_service, "get_or_create_product_for_formula", fake_get_or_create)
    csv_text = CSV_TEXT + 'Gel Igual,Marca B,cleanser,cleanser,morning,low," aqua, glycerin, decyl glucoside. ",cleanser,test\n'

    result = catalog_service.import_catalog_csv(SimpleNamespace(), csv_text)

    assert result.imported == 1
    assert result.reused == 1


def test_routine_contains_required_catalog_categories() -> None:
    profile = SkinProfileInput(skin_type="oily", sensitive_skin=False, acne_prone=True, barrier_compromised=False)
    products = [
        {"product_id": uuid4(), "name": "Cleanser", "brand": "A", "category": "cleanser", "routine_step": "cleanser", "ranking_score": 80, "irritation_risk": 10, "benefit_score": 50, "compatibility_score": 80, "ingredient_names": ["glycerin"]},
        {"product_id": uuid4(), "name": "Moisturizer", "brand": "A", "category": "moisturizer", "routine_step": "moisturizer", "ranking_score": 82, "irritation_risk": 10, "benefit_score": 70, "compatibility_score": 80, "ingredient_names": ["ceramide np"]},
        {"product_id": uuid4(), "name": "SPF", "brand": "A", "category": "sunscreen", "routine_step": "sunscreen", "ranking_score": 85, "irritation_risk": 10, "benefit_score": 70, "compatibility_score": 80, "ingredient_names": ["zinc oxide"]},
    ]

    morning, _night = select_best_products_for_routine(products, profile, "acne", 5)

    assert {"cleanser", "moisturizer", "sunscreen"}.issubset({item["routine_type"] for item in morning})


def test_sunscreen_appears_in_morning_from_catalog_metadata() -> None:
    profile = SkinProfileInput(skin_type="oily", sensitive_skin=False, acne_prone=False, barrier_compromised=False)
    sunscreen = {"product_id": uuid4(), "name": "Daily Shield", "brand": "A", "category": "sunscreen", "routine_step": "sunscreen", "ranking_score": 90, "irritation_risk": 5, "benefit_score": 70, "compatibility_score": 90, "ingredient_names": ["glycerin"]}

    morning, _night = select_best_products_for_routine([sunscreen], profile, "barrier", 5)

    assert any(item["routine_type"] == "sunscreen" for item in morning)


def test_catalog_products_are_filtered_by_category(monkeypatch) -> None:
    monkeypatch.setattr(
        catalog_service,
        "list_catalog_products",
        lambda db, **kwargs: [fake_product("SPF", "Aqua, Zinc Oxide", category=kwargs["category"])],
    )

    result = catalog_service.list_catalog(SimpleNamespace(), category="sunscreen")

    assert result[0].category == "sunscreen"


def test_products_without_raw_ingredient_list_do_not_enter_recommendations(monkeypatch) -> None:
    monkeypatch.setattr(
        recommendation_service,
        "list_products_with_formulas",
        lambda db, limit=100: [fake_product("Sem Formula", None), fake_product("Com Formula", "Aqua, Glycerin")],
    )
    monkeypatch.setattr(recommendation_service, "list_ingredients", lambda db: [])
    monkeypatch.setattr(
        recommendation_service,
        "insights_for_engine",
        lambda db, user_id: {"common_triggers": set(), "well_tolerated_ingredients": set()},
    )
    monkeypatch.setattr(
        recommendation_service,
        "analyze_formula",
        lambda parsed, skin_profile, personal_insights=None: {
            "compatibility_score": 80,
            "irritation_risk": 0.1,
            "acne_risk": 0.1,
            "benefit_score": 0.5,
            "positive_ingredients": [],
        },
    )
    profile = SkinProfileInput(skin_type="oily", sensitive_skin=False, acne_prone=False, barrier_compromised=False)

    result = recommendation_service.recommendation_analyses(
        SimpleNamespace(),
        SimpleNamespace(skin_profile=profile, exclude_ingredients=[], main_goal="barrier", limit=5),
    )

    assert [item["name"] for item in result] == ["Com Formula"]
