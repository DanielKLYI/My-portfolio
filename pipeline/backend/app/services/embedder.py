"""Embedding generation using sentence-transformers (runs locally, no API cost)."""
from __future__ import annotations
from sentence_transformers import SentenceTransformer
from ..config import settings

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def embed_chapter(title: str, extracted: dict) -> list[float]:
    """Build a representative text for the chapter and return its embedding."""
    parts = [f"Chapter: {title}"]

    for key in ("diseases", "medications", "labs", "interventions",
                "nursing_diagnoses", "patient_education", "safety_concerns", "clinical_judgment"):
        items = extracted.get(key, [])
        if items:
            label = key.replace("_", " ").title()
            parts.append(f"{label}: {'; '.join(items[:10])}")

    nclex = extracted.get("nclex_category", "")
    if nclex:
        parts.append(f"NCLEX: {nclex}")

    text = "\n".join(parts)
    model = _get_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def embed_query(query: str) -> list[float]:
    model = _get_model()
    vector = model.encode(query, normalize_embeddings=True)
    return vector.tolist()
