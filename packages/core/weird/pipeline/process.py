from __future__ import annotations

from datetime import datetime, timezone

from slugify import slugify
from sqlalchemy.orm import Session

from weird.clustering import ClusterMember, cluster_items
from weird.constants import Category, StoryStatus
from weird.embeddings import embed_text
from weird.models import Article, Story, StorySource, StoryTimeline
from weird.scoring import extract_tags, score_item
from weird.textutil import tokenize
from weird.vectorstore import upsert_article_embedding
from weird.db import get_engine


def _entities(text: str) -> set[str]:
    tokens = [t for t in tokenize(text) if t[0].isalpha() and len(t) > 3]
    return set(tokens[:40])


def process_articles(session: Session) -> dict[str, int]:
    articles = session.query(Article).all()
    members: list[ClusterMember] = []
    article_by_url: dict[str, Article] = {}
    for article in articles:
        blob = f"{article.title} {article.summary} {article.content[:1500]}"
        embedding = embed_text(blob)
        article.embedding = embedding
        try:
            upsert_article_embedding(get_engine(), article.id, embedding)
        except Exception:
            pass
        members.append(
            ClusterMember(
                key=str(article.id),
                title=article.title,
                url=article.canonical_url,
                embedding=embedding,
                entities=_entities(blob),
            )
        )
        article_by_url[article.canonical_url] = article

    clusters = cluster_items(members)
    created = 0
    updated = 0
    for cluster in clusters:
        articles_in = [article_by_url[m.url] for m in cluster if m.url in article_by_url]
        if not articles_in:
            continue
        primary = articles_in[0]
        cluster_key = sorted(a.canonical_url for a in articles_in)[0][:256]
        story = session.query(Story).filter_by(cluster_key=cluster_key).one_or_none()
        blob = " ".join(f"{a.title} {a.summary} {a.content[:800]}" for a in articles_in)
        tags = extract_tags(blob)
        category = _guess_category(blob, tags)
        source = primary.source
        credibility = source.credibility_score if source else 0.5
        extra = primary.extra or {}
        breakdown = score_item(
            title=primary.title,
            text=blob,
            category=category,
            credibility=credibility,
            stars=extra.get("stars"),
            comments=extra.get("comments") or extra.get("score"),
            source_count=len(articles_in),
            entities=list(_entities(blob)),
        )
        if story is None:
            slug = _unique_slug(session, slugify(primary.title) or f"story-{primary.id}")
            story = Story(
                title=primary.title[:512],
                slug=slug,
                dek=primary.summary[:280] if primary.summary else primary.title,
                description=(primary.summary or primary.content or "")[:800],
                category=category,
                cluster_key=cluster_key,
                status=StoryStatus.CLUSTERED,
                is_demo=False,
                analysis={},
            )
            session.add(story)
            session.flush()
            created += 1
        else:
            updated += 1
        story.signal_score = breakdown.signal
        story.cracked_score = breakdown.cracked
        story.rabbit_hole_score = breakdown.rabbit_hole
        story.tags = tags
        story.extra = {
            **(story.extra or {}),
            "dimensions": breakdown.dimensions,
            "contributions": breakdown.contributions,
            "weights": breakdown.weights,
            "score_explanations": breakdown.explanations,
            "rabbit_paths": breakdown.rabbit_paths,
            "cracked_blurb": breakdown.cracked_blurb,
            "embedding": embed_text(f"{story.title} {blob[:1200]}"),
        }
        existing_urls = {s.url for s in story.sources}
        for article in articles_in:
            if article.url in existing_urls:
                continue
            session.add(
                StorySource(
                    story_id=story.id,
                    article_id=article.id,
                    role="primary" if article.id == primary.id else "supporting",
                    url=article.url,
                    title=article.title,
                    credibility_kind=article.source.credibility_kind if article.source else "secondary_reporting",
                    credibility_score=article.source.credibility_score if article.source else 0.5,
                )
            )
            existing_urls.add(article.url)
            if story.timeline:
                session.add(
                    StoryTimeline(
                        story_id=story.id,
                        occurred_at=article.published_at or datetime.now(timezone.utc),
                        headline="New source joined the cluster",
                        body=article.title,
                        source_url=article.url,
                    )
                )
        if not story.timeline:
            session.add(
                StoryTimeline(
                    story_id=story.id,
                    occurred_at=primary.published_at or datetime.now(timezone.utc),
                    headline="First observed in the discovery pipeline",
                    body=primary.title,
                    source_url=primary.url,
                )
            )
        # Do not demote analyzed/selected/published stories back to clustered.
        if story.status in {
            StoryStatus.CANDIDATE,
            StoryStatus.CLUSTERED,
            StoryStatus.REJECTED,
        } or not story.status:
            story.status = StoryStatus.CLUSTERED
    session.flush()
    return {"clusters": len(clusters), "stories_created": created, "stories_updated": updated}


def _guess_category(blob: str, tags: list[str]) -> str:
    lower = blob.lower()
    rules = [
        (Category.BREAK, ["cve", "vulnerability", "exploit", "advisory"]),
        (Category.LEAK, ["leak", "rumor", "allegedly"]),
        (Category.LANG, ["compiler", "type system", "programming language", "interpreter"]),
        (Category.AI, ["llm", "transformer", "model", "inference", "training"]),
        (Category.MACHINE, ["cpu", "gpu", "fpga", "asic", "riscv", "firmware"]),
        (Category.LAB, ["arxiv", "we present", "paper"]),
        (Category.WATCH, ["youtube", "talk", "conference video"]),
        (Category.WHY, ["from scratch", "in c ", "unnecessary", "just for fun"]),
        (Category.DEEP, ["kernel", "abi", "filesystem", "microarchitecture"]),
        (Category.SOURCE, ["github.com", "open source"]),
        (Category.BUILD, ["rewrote", "implemented", "built"]),
    ]
    for cat, needles in rules:
        if any(n in lower for n in needles):
            return cat
    if "Rust" in tags or "C" in tags:
        return Category.BUILD
    return Category.SOURCE


def _unique_slug(session: Session, base: str) -> str:
    slug = base[:480]
    i = 2
    while session.query(Story).filter_by(slug=slug).one_or_none():
        slug = f"{base[:470]}-{i}"
        i += 1
    return slug
