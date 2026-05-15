from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.db.base import Base
from app.db.seed import seed_ingredients
from app.db.session import SessionLocal, engine
from app.modules.agent import models as agent_models
from app.modules.agent.router import router as agent_router
from app.modules.catalog.router import router as catalog_router
from app.modules.catalog.seed import seed_catalog_products
from app.modules.analysis_records import models as analysis_record_models
from app.modules.analysis.router import router as analysis_router
from app.modules.feedback import models as feedback_models
from app.modules.formula_cache import models as formula_cache_models
from app.modules.formulas.router import router as formulas_router
from app.modules.ingredients.router import router as ingredients_router
from app.modules.insights.router import router as insights_router
from app.modules.products import models as product_models
from app.modules.personalization import models as personalization_models
from app.modules.products.router import router as products_router
from app.modules.recommendations.router import router as recommendations_router
from app.modules.routines.router import router as routines_router


def ensure_catalog_columns() -> None:
    statements = [
        "ALTER TABLE products ALTER COLUMN raw_ingredient_list DROP NOT NULL",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS category VARCHAR(80)",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS routine_step VARCHAR(80)",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS usage_periods JSONB NOT NULL DEFAULT '[]'::jsonb",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS price_range VARCHAR(40)",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS tags JSONB NOT NULL DEFAULT '[]'::jsonb",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS is_active_treatment BOOLEAN NOT NULL DEFAULT false",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS is_sunscreen BOOLEAN NOT NULL DEFAULT false",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS is_moisturizer BOOLEAN NOT NULL DEFAULT false",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS is_cleanser BOOLEAN NOT NULL DEFAULT false",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS source VARCHAR(80)",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS source_url TEXT",
        "ALTER TABLE products ADD COLUMN IF NOT EXISTS catalog_status VARCHAR(40) NOT NULL DEFAULT 'active'",
        "CREATE INDEX IF NOT EXISTS ix_products_category ON products (category)",
        "CREATE INDEX IF NOT EXISTS ix_products_routine_step ON products (routine_step)",
        "CREATE INDEX IF NOT EXISTS ix_products_price_range ON products (price_range)",
        "CREATE INDEX IF NOT EXISTS ix_products_catalog_status ON products (catalog_status)",
    ]
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def ensure_agent_columns() -> None:
    statements = [
        "ALTER TABLE agent_messages ADD COLUMN IF NOT EXISTS confidence VARCHAR(20)",
        "ALTER TABLE agent_messages ADD COLUMN IF NOT EXISTS user_context_snapshot JSONB",
    ]
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=engine)
    ensure_catalog_columns()
    ensure_agent_columns()
    db = SessionLocal()
    try:
        seed_ingredients(db)
        seed_catalog_products(db)
    finally:
        db.close()
    yield


app = FastAPI(title="SkinMatch AI API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(ingredients_router)
app.include_router(formulas_router)
app.include_router(analysis_router)
app.include_router(insights_router)
app.include_router(products_router)
app.include_router(recommendations_router)
app.include_router(routines_router)
app.include_router(agent_router)
app.include_router(catalog_router)
