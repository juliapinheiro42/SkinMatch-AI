from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.catalog.schemas import CatalogImportResult, CatalogProductResponse
from app.modules.catalog.service import import_catalog_csv, list_catalog


router = APIRouter(prefix="/catalog", tags=["catalog"])


async def _csv_text_from_request(request: Request) -> str:
    body = await request.body()
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" not in content_type:
        return body.decode("utf-8-sig")

    text = body.decode("utf-8-sig", errors="ignore")
    marker = "\r\n\r\n"
    start = text.find(marker)
    if start == -1:
        return text
    payload = text[start + len(marker) :]
    end = payload.rfind("\r\n--")
    return payload[:end].strip() if end != -1 else payload.strip()


@router.post("/import-csv", response_model=CatalogImportResult)
async def import_csv(request: Request, db: Session = Depends(get_db)) -> CatalogImportResult:
    return import_catalog_csv(db, await _csv_text_from_request(request))


@router.get("/products", response_model=list[CatalogProductResponse])
def products(
    db: Session = Depends(get_db),
    category: str | None = None,
    routine_step: str | None = None,
    tag: str | None = None,
    price_range: str | None = None,
    is_active_treatment: bool | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[CatalogProductResponse]:
    return list_catalog(
        db,
        category=category,
        routine_step=routine_step,
        tag=tag,
        price_range=price_range,
        is_active_treatment=is_active_treatment,
        limit=limit,
    )
