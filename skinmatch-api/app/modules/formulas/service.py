import hashlib
import re


def normalize_formula_text(raw_ingredient_list: str) -> str:
    ingredients = [
        re.sub(r"\s+", " ", item.strip().lower()).removesuffix(".")
        for item in raw_ingredient_list.split(",")
        if item.strip()
    ]
    return ", ".join(ingredients)


def formula_hash(raw_ingredient_list: str) -> str:
    normalized = normalize_formula_text(raw_ingredient_list)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def product_normalized_name(name: str, brand: str | None = None) -> str:
    value = f"{brand or ''} {name}".strip().lower()
    return re.sub(r"\s+", " ", value)
