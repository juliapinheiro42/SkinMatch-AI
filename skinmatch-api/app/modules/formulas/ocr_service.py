import re
from io import BytesIO

try:
    from PIL import Image
    import pytesseract
except ImportError:
    Image = None
    pytesseract = None


INGREDIENT_MARKERS = ("ingredients", "ingredientes", "ingredientes:", "ingredients:")


def clean_ingredient_text(text: str) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    lower = compact.lower()

    start = -1
    for marker in INGREDIENT_MARKERS:
        marker_index = lower.find(marker)
        if marker_index >= 0:
            start = marker_index + len(marker)
            break

    ingredient_text = compact[start:] if start >= 0 else compact
    ingredient_text = re.split(r"(modo de uso|directions|warning|advertencias|precautions)", ingredient_text, flags=re.I)[0]
    ingredient_text = ingredient_text.replace(";", ",")
    ingredient_text = re.sub(r"\s*,\s*", ", ", ingredient_text)
    ingredient_text = re.sub(r"[^A-Za-zÀ-ÿ0-9,\.\-\s]", " ", ingredient_text)
    ingredient_text = re.sub(r"\s+", " ", ingredient_text)
    return ingredient_text.strip(" ,.")


def extract_text_from_image(image_bytes: bytes) -> str:
    if Image is None or pytesseract is None:
        return ""

    try:
        image = Image.open(BytesIO(image_bytes))
        return pytesseract.image_to_string(image)
    except Exception:
        return ""


def ocr_dependencies_ready() -> bool:
    return Image is not None and pytesseract is not None


def ocr_formula_from_image(image_bytes: bytes) -> dict[str, str]:
    extracted_text = extract_text_from_image(image_bytes)
    cleaned = clean_ingredient_text(extracted_text)
    return {
        "extracted_text": extracted_text,
        "cleaned_ingredient_list": cleaned or extracted_text.strip(),
    }
