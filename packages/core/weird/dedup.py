from __future__ import annotations

from collections.abc import Iterable, Sequence

from weird.embeddings import cosine, hashed_embedding
from weird.textutil import canonicalize_url, content_hash, title_similarity


def is_duplicate(
    *,
    url: str,
    title: str,
    text: str,
    existing: Iterable[tuple[str, str, str]],
    title_threshold: float = 0.88,
    existing_embeddings: Sequence[tuple[str, list[float]]] | None = None,
    semantic_threshold: float = 0.93,
) -> bool:
    canon = canonicalize_url(url)
    hashed = content_hash(f"{title}\n{text}")
    for e_url, e_title, e_hash in existing:
        if canon and canon == canonicalize_url(e_url):
            return True
        if hashed and hashed == e_hash:
            return True
        if title_similarity(title, e_title) >= title_threshold:
            return True
    if existing_embeddings:
        vec = hashed_embedding(f"{title}\n{text}")
        for e_title, e_vec in existing_embeddings:
            if cosine(vec, e_vec) >= semantic_threshold and title_similarity(title, e_title) >= 0.35:
                return True
    return False
