from fastapi import APIRouter, HTTPException, Request

from app.modules.formulas.ocr_service import ocr_dependencies_ready, ocr_formula_from_image


router = APIRouter(prefix="/formulas", tags=["formulas"])


@router.post("/ocr")
async def ocr_formula(request: Request) -> dict[str, str]:
    if not ocr_dependencies_ready():
        raise HTTPException(
            status_code=503,
            detail="OCR dependencies are not available. Rebuild the API image or install Pillow, pytesseract and Tesseract.",
        )

    try:
        form = await request.form()
    except AssertionError as exc:
        raise HTTPException(
            status_code=503,
            detail="python-multipart is required for OCR uploads. Rebuild the API image or install python-multipart.",
        ) from exc

    image = form.get("image")
    if image is None or not hasattr(image, "read"):
        raise HTTPException(status_code=400, detail="image file is required")

    content = await image.read()
    result = ocr_formula_from_image(content)
    if not result["extracted_text"].strip():
        raise HTTPException(
            status_code=422,
            detail="OCR did not extract readable text from this image. Try a sharper, well-lit photo of the ingredients list.",
        )
    return result
