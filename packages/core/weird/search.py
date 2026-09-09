from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session, joinedload

from weird.embeddings import cosine, hashed_embedding, hybrid_rank_score, tokenize
from weird.models import Story


@dataclass
class SearchHit:
    story: Story
    score: float
    keyword_score: float
    semantic_score: float
    mode: str


def story_search_blob(story: Story) -> str:
    analysis = story.analysis or {}
    extra = story.extra or {}
    parts = [
        story.title,
        story.dek,
        story.description,
        " ".join(story.tags or []),
        story.category,
        str(analysis.get("how_it_works", "")),
        str(analysis.get("under_the_hood", "")),
        str(analysis.get("what_happened", "")),
        " ".join(extra.get("rabbit_paths") or []),
        " ".join(analysis.get("rabbit_holes") or []) if isinstance(analysis.get("rabbit_holes"), list) else "",
    ]
    return " ".join(p for p in parts if p)


def hybrid_search(
    session: Session,
    *,
    q: str = "",
    category: str | None = None,
    tag: str | None = None,
    min_score: float | None = None,
    confidence: str | None = None,
    limit: int = 50,
) -> list[SearchHit]:
    """Keyword (token overlap / TF-IDF-ish) + hashed semantic + metadata filters."""
    query = session.query(Story).options(joinedload(Story.sources))
    if category:
        query = query.filter(Story.category == category.upper())
    if confidence:
        query = query.filter(Story.confidence == confidence)
    if min_score is not None:
        query = query.filter(Story.signal_score >= min_score)
    stories = query.all()
    if tag:
        needle = tag.lower()
        stories = [s for s in stories if needle in [t.lower() for t in (s.tags or [])]]

    needle = (q or "").strip()
    if not needle:
        ranked = sorted(stories, key=lambda s: s.signal_score, reverse=True)[:limit]
        return [
            SearchHit(story=s, score=s.signal_score, keyword_score=0.0, semantic_score=0.0, mode="metadata")
            for s in ranked
        ]

    query_tokens = tokenize(needle)
    query_vec = hashed_embedding(needle)
    hits: list[SearchHit] = []
    for story in stories:
        blob = story_search_blob(story)
        doc_tokens = tokenize(blob)
        keyword, semantic, combined = hybrid_rank_score(query_tokens, doc_tokens, query_vec, _story_embedding(story, blob))
        if keyword <= 0 and semantic < 0.35:
            continue
        # Mild boost for high signal so hybrid stays editorial.
        score = combined + story.signal_score / 500.0
        hits.append(
            SearchHit(
                story=story,
                score=score,
                keyword_score=keyword,
                semantic_score=semantic,
                mode="hybrid",
            )
        )
    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[:limit]


def _story_embedding(story: Story, blob: str) -> list[float]:
    extra = story.extra or {}
    stored = extra.get("embedding")
    if isinstance(stored, list) and stored and all(isinstance(x, (int, float)) for x in stored):
        return [float(x) for x in stored]
    return hashed_embedding(blob)


def search_mode_label() -> dict[str, Any]:
    from weird.embeddings import embedding_backend

    backend = embedding_backend()
    return {
        "search": "hybrid",
        "keyword": "token-overlap",
        "semantic": backend["name"],
        "semantic_available": backend["available"],
        "vector_store": backend.get("vector_store", "json"),
    }
