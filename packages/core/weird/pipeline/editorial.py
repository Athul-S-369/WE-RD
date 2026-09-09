from __future__ import annotations

from collections import defaultdict

from weird.constants import EDITION_SECTIONS
from weird.models import Story

CATEGORY_TO_SECTION = {
    "BUILD": "HOW THE HELL DID THEY BUILD THIS?",
    "WHY": "WHY DOES THIS EXIST?",
    "DEEP": "DEEP END",
    "BREAK": "BREAK",
    "LANG": "LANG",
    "MACHINE": "MACHINE",
    "AI": "AI",
    "LAB": "LAB",
    "SOURCE": "SOURCE",
    "WATCH": "WATCH",
    "LEAK": "BREAK",
}


def select_edition_stories(candidates: list[Story], max_stories: int = 16) -> list[tuple[str, Story, bool]]:
    """Editorial optimization: scores + diversity + optional AI/heuristic evaluator. Quality over fill."""
    ranked = sorted(
        candidates,
        key=lambda s: (s.signal_score * 0.55 + s.cracked_score * 0.2 + s.rabbit_hole_score * 0.25),
        reverse=True,
    )
    # Drop weak stories rather than pad.
    floor = 48.0
    ranked = [s for s in ranked if s.signal_score >= floor or s.cracked_score >= 70]
    # Honor structured editorial evaluator when present.
    filtered: list[Story] = []
    for story in ranked:
        editorial = (story.extra or {}).get("editorial") or {}
        if editorial and editorial.get("keep") is False:
            continue
        if editorial and editorial.get("publish_ready") is False and story.signal_score < 75:
            continue
        filtered.append(story)
    ranked = filtered or ranked
    chosen: list[Story] = []
    used_titles: list[str] = []
    used_categories: dict[str, int] = defaultdict(int)
    for story in ranked:
        if len(chosen) >= max_stories:
            break
        if _redundant(story, chosen, used_titles):
            continue
        if used_categories[story.category] >= 2 and story.signal_score < 80:
            continue
        chosen.append(story)
        used_titles.append(story.title)
        used_categories[story.category] += 1

    if not chosen:
        return []

    featured = max(chosen, key=lambda s: s.signal_score * 0.4 + s.cracked_score * 0.6)
    assignments: list[tuple[str, Story, bool]] = [
        ("THE BIG WE-RD", featured, True),
    ]
    remaining = [s for s in chosen if s.id != featured.id]
    rabbit = max(remaining, key=lambda s: s.rabbit_hole_score, default=None)
    for story in remaining:
        section = CATEGORY_TO_SECTION.get(story.category, "SOURCE")
        assignments.append((section, story, False))
    if rabbit and all(a[0] != "RABBIT HOLE" for a in assignments):
        assignments.append(("RABBIT HOLE", rabbit, False))

    # Stable editorial order
    order = {name: i for i, name in enumerate(EDITION_SECTIONS)}
    assignments.sort(key=lambda row: (0 if row[2] else 1, order.get(row[0], 99), -row[1].signal_score))
    return assignments


def _redundant(story: Story, chosen: list[Story], titles: list[str]) -> bool:
    from weird.textutil import title_similarity

    for other in chosen:
        if story.cluster_key and other.cluster_key and story.cluster_key == other.cluster_key:
            return True
        if title_similarity(story.title, other.title) > 0.55:
            return True
        overlap = set(story.tags or []) & set(other.tags or [])
        if story.category == other.category and len(overlap) >= 4:
            return True
    return False
