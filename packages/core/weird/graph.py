from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session, joinedload

from weird.embeddings import cosine, hashed_embedding
from weird.models import Story
from weird.search import story_search_blob


@dataclass
class GraphNode:
    kind: str
    id: str
    label: str
    url: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    source: str
    target: str
    relation: str
    weight: float = 1.0


@dataclass
class SourceGraph:
    story_slug: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    related: list[dict[str, Any]]


def build_source_graph(session: Session, story: Story, *, related_limit: int = 6) -> SourceGraph:
    nodes: list[GraphNode] = [
        GraphNode(kind="story", id=f"story:{story.slug}", label=story.title, meta={"category": story.category})
    ]
    edges: list[GraphEdge] = []

    for src in story.sources or []:
        nid = f"source:{src.url}"
        nodes.append(
            GraphNode(
                kind="source",
                id=nid,
                label=src.title or src.url,
                url=src.url,
                meta={"role": src.role, "credibility_kind": src.credibility_kind},
            )
        )
        edges.append(GraphEdge(f"story:{story.slug}", nid, src.role or "supporting", src.credibility_score or 0.5))

    for project in story.projects or []:
        nid = f"project:{project.url}"
        nodes.append(
            GraphNode(
                kind="project",
                id=nid,
                label=project.name,
                url=project.url,
                meta={"host": project.host, "stars": project.stars, "language": project.language},
            )
        )
        edges.append(GraphEdge(f"story:{story.slug}", nid, "code", 1.0))

    for video in story.videos or []:
        nid = f"video:{video.video_id}"
        nodes.append(
            GraphNode(
                kind="video",
                id=nid,
                label=video.title,
                url=video.url,
                meta={"channel": video.channel, "technical": video.technical},
            )
        )
        edges.append(GraphEdge(f"story:{story.slug}", nid, "talk", video.relevance_score or 0.5))

    for tag in story.tags or []:
        nid = f"concept:{tag.lower()}"
        nodes.append(GraphNode(kind="concept", id=nid, label=tag))
        edges.append(GraphEdge(f"story:{story.slug}", nid, "tagged", 0.8))

    for path in (story.extra or {}).get("rabbit_paths") or []:
        nid = f"concept:{str(path).lower()}"
        if not any(n.id == nid for n in nodes):
            nodes.append(GraphNode(kind="concept", id=nid, label=str(path)))
            edges.append(GraphEdge(f"story:{story.slug}", nid, "rabbit", 0.9))

    related = related_stories(session, story, limit=related_limit)
    for item in related:
        nid = f"story:{item['slug']}"
        if not any(n.id == nid for n in nodes):
            nodes.append(
                GraphNode(
                    kind="related_story",
                    id=nid,
                    label=item["title"],
                    url=f"/story/{item['slug']}",
                    meta={"score": item["score"], "shared": item["shared"]},
                )
            )
            edges.append(GraphEdge(f"story:{story.slug}", nid, "related", item["score"]))

    return SourceGraph(story_slug=story.slug, nodes=nodes, edges=edges, related=related)


def related_stories(session: Session, story: Story, *, limit: int = 6) -> list[dict[str, Any]]:
    """Lightweight knowledge links by tags, rabbit paths, category, and embedding."""
    others = (
        session.query(Story)
        .options(joinedload(Story.sources))
        .filter(Story.id != story.id)
        .all()
    )
    tags = {t.lower() for t in (story.tags or [])}
    paths = {str(p).lower() for p in ((story.extra or {}).get("rabbit_paths") or [])}
    blob = story_search_blob(story)
    vec = (story.extra or {}).get("embedding")
    if not isinstance(vec, list):
        vec = hashed_embedding(blob)

    scored: list[dict[str, Any]] = []
    for other in others:
        other_tags = {t.lower() for t in (other.tags or [])}
        other_paths = {str(p).lower() for p in ((other.extra or {}).get("rabbit_paths") or [])}
        shared_tags = sorted(tags & other_tags)
        shared_paths = sorted(paths & other_paths)
        shared = shared_tags + [p for p in shared_paths if p not in shared_tags]
        tag_score = len(shared_tags) * 0.18
        path_score = len(shared_paths) * 0.12
        cat_score = 0.15 if other.category == story.category else 0.0
        other_blob = story_search_blob(other)
        other_vec = (other.extra or {}).get("embedding")
        if not isinstance(other_vec, list):
            other_vec = hashed_embedding(other_blob)
        sem = cosine(vec, other_vec)
        score = tag_score + path_score + cat_score + 0.55 * sem
        if score < 0.28 and not shared:
            continue
        scored.append(
            {
                "slug": other.slug,
                "title": other.title,
                "category": other.category,
                "signal_score": other.signal_score,
                "score": round(score, 4),
                "shared": shared[:8],
            }
        )
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]


def concept_index(session: Session) -> list[dict[str, Any]]:
    freq: dict[str, dict[str, Any]] = {}
    for story in session.query(Story).all():
        concepts = list(story.tags or []) + list((story.extra or {}).get("rabbit_paths") or [])
        for concept in concepts:
            key = str(concept).strip()
            if not key:
                continue
            bucket = freq.setdefault(key, {"concept": key, "count": 0, "stories": []})
            bucket["count"] += 1
            if len(bucket["stories"]) < 8:
                bucket["stories"].append({"slug": story.slug, "title": story.title})
    return sorted(freq.values(), key=lambda x: -x["count"])
