from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from weird.dedup import is_duplicate
from weird.ingestion.catalog import DEFAULT_SOURCES, build_adapter
from weird.logging import get_logger
from weird.models import Article, Source
from weird.security import is_safe_http_url, sanitize_html
from weird.textutil import canonicalize_url, content_hash

log = get_logger("ingestion")


def ensure_sources(session: Session) -> None:
    for spec in DEFAULT_SOURCES:
        existing = session.query(Source).filter_by(name=spec.name).one_or_none()
        if existing:
            continue
        session.add(
            Source(
                name=spec.name,
                type=spec.type,
                url=spec.url,
                credibility_score=spec.credibility_score,
                credibility_kind=spec.credibility_kind,
                extra={},
            )
        )
    session.flush()


def ingest_all(session: Session) -> dict[str, int]:
    ensure_sources(session)
    metrics = {"fetched": 0, "stored": 0, "duplicates": 0, "failures": 0, "rejected_urls": 0}
    sources = session.query(Source).filter_by(active=True).all()
    existing = [
        (row.url, row.title, row.content_hash or "")
        for row in session.query(Article.url, Article.title, Article.content_hash).all()
    ]
    existing_urls = {canonicalize_url(u) for u, _, _ in existing if u}

    for source in sources:
        spec = next((s for s in DEFAULT_SOURCES if s.name == source.name), None)
        if spec is None:
            continue
        try:
            adapter = build_adapter(spec)
            items = adapter.fetch()
            source.last_fetched_at = datetime.now(timezone.utc)
            source.last_error = None
            metrics["fetched"] += len(items)
        except Exception as exc:  # noqa: BLE001 — isolated source failure
            log.warning("source_failed", source=source.name, error=str(exc))
            source.last_error = str(exc)[:2000]
            metrics["failures"] += 1
            continue

        for item in items:
            if not is_safe_http_url(item.url):
                metrics["rejected_urls"] += 1
                continue
            canon = canonicalize_url(item.url)
            if not canon or canon in existing_urls:
                metrics["duplicates"] += 1
                continue
            text_blob = f"{item.content or ''}\n{item.summary or ''}"
            if is_duplicate(url=item.url, title=item.title, text=text_blob, existing=existing):
                metrics["duplicates"] += 1
                continue

            clean_content = sanitize_html(item.content or "")[:20000]
            clean_summary = sanitize_html(item.summary or "")[:4000]
            hashed = content_hash(f"{item.title}\n{clean_content}\n{clean_summary}")
            article = Article(
                source_id=source.id,
                title=item.title[:512],
                url=item.url[:2048],
                canonical_url=canon[:2048],
                author=item.author,
                published_at=item.published_at,
                content=clean_content,
                summary=clean_summary,
                content_hash=hashed,
                extra=item.extra,
            )
            session.add(article)
            existing_urls.add(canon)
            existing.append((item.url, item.title, hashed))
            metrics["stored"] += 1
    session.flush()
    return metrics
