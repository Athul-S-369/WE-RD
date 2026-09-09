from __future__ import annotations

from weird.constants import CATEGORY_LABELS, Category, cracked_blurb
from weird.models import Edition, Story
from weird.schemas import (
    EditionListItem,
    EditionOut,
    EditionStoryOut,
    ProjectOut,
    StoryCard,
    StoryDetail,
    StorySourceOut,
    TimelineOut,
    VideoOut,
)


def to_card(story: Story) -> StoryCard:
    sources = story.sources or []
    primary = next((s.url for s in sources if s.role == "primary"), sources[0].url if sources else None)
    extra = story.extra or {}
    return StoryCard(
        slug=story.slug,
        title=story.title,
        dek=story.dek,
        description=story.description,
        category=story.category,
        category_label=CATEGORY_LABELS.get(Category(story.category), f"WE-RD / {story.category}"),
        signal_score=round(story.signal_score, 1),
        cracked_score=story.cracked_score,
        rabbit_hole_score=round(story.rabbit_hole_score, 1),
        confidence=story.confidence,
        tags=story.tags or [],
        is_demo=story.is_demo,
        cracked_blurb=extra.get("cracked_blurb") or cracked_blurb(story.cracked_score),
        primary_source=primary,
        score_dimensions=extra.get("dimensions") or {},
        processing_mode=extra.get("processing_mode"),
    )


def to_detail(
    story: Story,
    *,
    related: list[dict] | None = None,
    source_graph: dict | None = None,
) -> StoryDetail:
    card = to_card(story)
    extra = story.extra or {}
    breakdown = {
        "dimensions": extra.get("dimensions") or {},
        "contributions": extra.get("contributions") or {},
        "weights": extra.get("weights") or {},
        "explanations": extra.get("score_explanations") or {},
        "rabbit_paths": extra.get("rabbit_paths") or [],
    }
    return StoryDetail(
        **card.model_dump(),
        analysis=story.analysis or {},
        security=story.security,
        leak=story.leak,
        timeline=[TimelineOut.model_validate(t) for t in story.timeline],
        videos=[VideoOut.model_validate(v) for v in story.videos],
        projects=[ProjectOut.model_validate(p) for p in story.projects],
        sources=[StorySourceOut.model_validate(s) for s in story.sources],
        created_at=story.created_at,
        score_breakdown=breakdown,
        related=related or [],
        source_graph=source_graph or {},
        youtube_status=extra.get("youtube_status"),
        editorial=extra.get("editorial") or {},
    )


def to_edition(edition: Edition) -> EditionOut:
    rows = []
    for es in edition.stories:
        rows.append(
            EditionStoryOut(
                section=es.section,
                sort_order=es.sort_order,
                featured=es.featured,
                story=to_card(es.story),
            )
        )
    return EditionOut(
        issue_number=edition.issue_number,
        week_start=edition.week_start,
        week_end=edition.week_end,
        status=edition.status,
        published_at=edition.published_at,
        masthead=edition.masthead,
        week_in_numbers=edition.week_in_numbers or {},
        is_demo=edition.is_demo,
        stories=rows,
    )


def to_edition_list_item(edition: Edition) -> EditionListItem:
    return EditionListItem(
        issue_number=edition.issue_number,
        week_start=edition.week_start,
        week_end=edition.week_end,
        status=edition.status,
        published_at=edition.published_at,
        is_demo=edition.is_demo,
        story_count=len(edition.stories),
    )
