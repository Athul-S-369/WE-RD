from __future__ import annotations

from dataclasses import dataclass

from weird.embeddings import cosine
from weird.textutil import canonicalize_url, title_similarity


@dataclass
class ClusterMember:
    key: str
    title: str
    url: str
    embedding: list[float] | None
    entities: set[str]


def should_merge(a: ClusterMember, b: ClusterMember) -> bool:
    if canonicalize_url(a.url) and canonicalize_url(a.url) == canonicalize_url(b.url):
        return True
    title_sim = title_similarity(a.title, b.title)
    entity_overlap = 0.0
    if a.entities and b.entities:
        entity_overlap = len(a.entities & b.entities) / len(a.entities | b.entities)
    embed_sim = 0.0
    if a.embedding and b.embedding:
        embed_sim = cosine(a.embedding, b.embedding)
    if title_sim >= 0.72:
        return True
    if title_sim >= 0.45 and entity_overlap >= 0.4:
        return True
    if embed_sim >= 0.86 and title_sim >= 0.28:
        return True
    if embed_sim >= 0.92:
        return True
    return False


def cluster_items(items: list[ClusterMember]) -> list[list[ClusterMember]]:
    clusters: list[list[ClusterMember]] = []
    for item in items:
        placed = False
        for cluster in clusters:
            if any(should_merge(item, existing) for existing in cluster):
                cluster.append(item)
                placed = True
                break
        if not placed:
            clusters.append([item])
    return clusters
