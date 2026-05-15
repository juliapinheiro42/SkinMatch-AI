import hashlib
import math

import httpx

from app.config import settings
from app.modules.formulas.service import normalize_formula_text


def _deterministic_embedding(text: str, dimensions: int) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values = []
    for index in range(dimensions):
        byte = digest[index % len(digest)]
        values.append((byte / 127.5) - 1.0)
    norm = math.sqrt(sum(value * value for value in values)) or 1.0
    return [value / norm for value in values]


def generate_formula_embedding(raw_ingredient_list: str) -> list[float]:
    normalized = normalize_formula_text(raw_ingredient_list)

    if not settings.openai_api_key:
        return _deterministic_embedding(normalized, settings.embedding_dimensions)

    try:
        response = httpx.post(
            "https://api.openai.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.embedding_model,
                "input": normalized,
                "encoding_format": "float",
            },
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]
    except Exception:
        return _deterministic_embedding(normalized, settings.embedding_dimensions)
