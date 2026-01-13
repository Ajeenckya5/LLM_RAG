from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer

from .config import settings

_model: SentenceTransformer | None = None


def get_embedder() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def chunk_text(text: str, max_chars: int = 1200, overlap: int = 150) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []

    chunks: list[str] = []
    i = 0
    while i < len(text):
        j = min(len(text), i + max_chars)
        chunk = text[i:j].strip()
        if chunk:
            chunks.append(chunk)
        if j == len(text):
            break
        i = max(0, j - overlap)
    return chunks


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedder()
    vecs = model.encode([f"passage: {t}" for t in texts], normalize_embeddings=True)
    return vecs.astype(np.float32).tolist()


def embed_query(q: str) -> list[float]:
    model = get_embedder()
    v = model.encode([f"query: {q}"], normalize_embeddings=True)[0]
    return v.astype(np.float32).tolist()

