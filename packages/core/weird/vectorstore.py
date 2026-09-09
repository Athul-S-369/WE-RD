"""Optional pgvector helpers. JSON embeddings remain the default for SQLite demos."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine


def is_postgres(engine: Engine) -> bool:
    return engine.dialect.name == "postgresql"


def ensure_pgvector(engine: Engine) -> dict[str, Any]:
    """Enable pgvector extension when configured. Safe no-op on SQLite."""
    if not is_postgres(engine):
        return {"enabled": False, "reason": "not_postgres"}
    from weird.config import get_settings

    if not get_settings().weird_use_pgvector:
        return {"enabled": False, "reason": "weird_use_pgvector=false"}
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            # Side table keeps JSON Article.embedding as source of truth for dual-write.
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS article_embeddings (
                        article_id INTEGER PRIMARY KEY REFERENCES articles(id) ON DELETE CASCADE,
                        embedding vector(96),
                        updated_at TIMESTAMPTZ DEFAULT NOW()
                    )
                    """
                )
            )
        return {"enabled": True, "dim": 96, "table": "article_embeddings"}
    except Exception as exc:  # noqa: BLE001
        return {"enabled": False, "reason": str(exc)[:300]}


def upsert_article_embedding(engine: Engine, article_id: int, embedding: list[float]) -> bool:
    if not is_postgres(engine):
        return False
    from weird.config import get_settings

    if not get_settings().weird_use_pgvector:
        return False
    if not embedding:
        return False
    # Pad/truncate to 96 for the side table contract.
    vec = list(embedding[:96]) + [0.0] * max(0, 96 - len(embedding))
    literal = "[" + ",".join(f"{x:.8f}" for x in vec) + "]"
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO article_embeddings (article_id, embedding, updated_at)
                    VALUES (:id, CAST(:emb AS vector), NOW())
                    ON CONFLICT (article_id) DO UPDATE
                    SET embedding = EXCLUDED.embedding, updated_at = NOW()
                    """
                ),
                {"id": article_id, "emb": literal},
            )
        return True
    except Exception:
        return False
