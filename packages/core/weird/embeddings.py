from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from collections.abc import Sequence
from typing import Any

TOKEN_RE = re.compile(r"[a-z0-9+#]+")
DIM = 96


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN_RE.findall((text or "").lower()) if len(t) > 1]


def hashed_embedding(text: str, dim: int = DIM) -> list[float]:
    """Deterministic hashed bag-of-words embedding. No external model required."""
    vec = [0.0] * dim
    for token in tokenize(text):
        h = int(hashlib.md5(token.encode()).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if (h >> 8) % 2 == 0 else -1.0
        # Mild IDF-ish dampening via token length / rarity proxy
        weight = 1.0 + min(len(token), 12) / 12.0
        vec[idx] += sign * weight
    return _normalize(vec)


def tfidf_vectors(docs: Sequence[str]) -> tuple[list[list[float]], dict[str, int]]:
    """Build sparse-as-dense hashed TF-IDF vectors for a small corpus."""
    tokenized = [tokenize(d) for d in docs]
    df: Counter[str] = Counter()
    for toks in tokenized:
        df.update(set(toks))
    n = max(len(docs), 1)
    vocab = {tok: i for i, tok in enumerate(sorted(df))}
    # Cap vocab projection into fixed dim via hashing if huge
    dim = min(max(len(vocab), 32), 256)
    vectors: list[list[float]] = []
    for toks in tokenized:
        tf = Counter(toks)
        vec = [0.0] * dim
        length = max(sum(tf.values()), 1)
        for tok, count in tf.items():
            idf = math.log((1 + n) / (1 + df[tok])) + 1.0
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            idx = h % dim
            sign = 1.0 if (h >> 8) % 2 == 0 else -1.0
            vec[idx] += sign * (count / length) * idf
        vectors.append(_normalize(vec))
    return vectors, vocab


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def token_overlap(query_tokens: Sequence[str], doc_tokens: Sequence[str]) -> float:
    q = set(query_tokens)
    d = set(doc_tokens)
    if not q or not d:
        return 0.0
    return len(q & d) / len(q)


def bm25_lite(query_tokens: Sequence[str], doc_tokens: Sequence[str], avgdl: float = 80.0) -> float:
    """Lightweight BM25 without a global IDF table — good zero-dependency fallback."""
    if not query_tokens or not doc_tokens:
        return 0.0
    tf = Counter(doc_tokens)
    dl = len(doc_tokens)
    k1, b = 1.4, 0.75
    score = 0.0
    for term in set(query_tokens):
        f = tf.get(term, 0)
        if f == 0:
            continue
        # Pseudo-IDF: rarer-looking (longer) terms weigh slightly more
        idf = 1.2 + min(len(term), 10) / 10.0
        denom = f + k1 * (1 - b + b * dl / max(avgdl, 1.0))
        score += idf * (f * (k1 + 1)) / denom
    return score / max(len(set(query_tokens)), 1)


def hybrid_rank_score(
    query_tokens: Sequence[str],
    doc_tokens: Sequence[str],
    query_vec: Sequence[float],
    doc_vec: Sequence[float],
    *,
    keyword_weight: float = 0.55,
    semantic_weight: float = 0.45,
) -> tuple[float, float, float]:
    overlap = token_overlap(query_tokens, doc_tokens)
    bm25 = min(bm25_lite(query_tokens, doc_tokens) / 4.0, 1.0)
    keyword = 0.6 * overlap + 0.4 * bm25
    semantic = cosine(query_vec, doc_vec)
    combined = keyword_weight * keyword + semantic_weight * semantic
    return keyword, semantic, combined


def embed_text(text: str) -> list[float]:
    """Local-first embedding: optional sentence-transformers, else hashed BoW."""
    backend = embedding_backend()
    if backend["name"] == "sentence-transformers":
        model = _get_st_model()
        if model is not None:
            vec = model.encode(text or "", normalize_embeddings=True)
            return [float(x) for x in vec]
    return hashed_embedding(text)


def embedding_backend() -> dict[str, Any]:
    from weird.config import get_settings

    settings = get_settings()
    store = "pgvector" if settings.weird_use_pgvector else "json"
    if settings.weird_embedding_backend == "hashed":
        return {"name": "hashed-bow", "available": True, "vector_store": store, "dim": DIM}
    if settings.weird_embedding_backend in {"auto", "sentence-transformers"}:
        model = _get_st_model()
        if model is not None:
            dim = int(getattr(model, "get_sentence_embedding_dimension", lambda: 384)())
            return {
                "name": "sentence-transformers",
                "available": True,
                "vector_store": store,
                "dim": dim,
                "model": settings.weird_local_embedding_model,
            }
        if settings.weird_embedding_backend == "sentence-transformers":
            return {
                "name": "hashed-bow",
                "available": True,
                "vector_store": store,
                "dim": DIM,
                "fallback_reason": "sentence-transformers not installed or model load failed",
            }
    return {"name": "hashed-bow", "available": True, "vector_store": store, "dim": DIM}


_ST_MODEL = None
_ST_TRIED = False


def _get_st_model():
    global _ST_MODEL, _ST_TRIED
    if _ST_TRIED:
        return _ST_MODEL
    _ST_TRIED = True
    try:
        from sentence_transformers import SentenceTransformer

        from weird.config import get_settings

        _ST_MODEL = SentenceTransformer(get_settings().weird_local_embedding_model)
    except Exception:
        _ST_MODEL = None
    return _ST_MODEL


def _normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]
