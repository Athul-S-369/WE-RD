from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str
    url: str
    credibility_score: float
    credibility_kind: str
    active: bool
    last_error: str | None = None


class VideoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    video_id: str
    title: str
    channel: str
    url: str
    duration_seconds: int | None = None
    published_at: datetime | None = None
    description: str = ""
    thumbnail: str | None = None
    relevance_score: float = 0
    technical: bool = True


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    url: str
    host: str
    stars: int | None = None
    language: str | None = None
    description: str = ""


class TimelineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    occurred_at: datetime
    headline: str
    body: str = ""
    source_url: str | None = None


class StorySourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role: str
    url: str
    title: str
    credibility_kind: str
    credibility_score: float


class StoryCard(BaseModel):
    slug: str
    title: str
    dek: str
    description: str
    category: str
    category_label: str
    signal_score: float
    cracked_score: int
    rabbit_hole_score: float
    confidence: str
    tags: list[str]
    is_demo: bool
    cracked_blurb: str
    primary_source: str | None = None
    score_dimensions: dict[str, float] = Field(default_factory=dict)
    processing_mode: str | None = None


class StoryDetail(StoryCard):
    analysis: dict[str, Any]
    security: dict[str, Any] | None = None
    leak: dict[str, Any] | None = None
    timeline: list[TimelineOut] = Field(default_factory=list)
    videos: list[VideoOut] = Field(default_factory=list)
    projects: list[ProjectOut] = Field(default_factory=list)
    sources: list[StorySourceOut] = Field(default_factory=list)
    created_at: datetime | None = None
    score_breakdown: dict[str, Any] = Field(default_factory=dict)
    related: list[dict[str, Any]] = Field(default_factory=list)
    source_graph: dict[str, Any] = Field(default_factory=dict)
    youtube_status: str | None = None
    editorial: dict[str, Any] = Field(default_factory=dict)


class EditionStoryOut(BaseModel):
    section: str
    sort_order: int
    featured: bool
    story: StoryCard


class EditionOut(BaseModel):
    issue_number: int
    week_start: datetime
    week_end: datetime
    status: str
    published_at: datetime | None
    masthead: str
    week_in_numbers: dict[str, Any]
    is_demo: bool
    stories: list[EditionStoryOut] = Field(default_factory=list)


class EditionListItem(BaseModel):
    issue_number: int
    week_start: datetime
    week_end: datetime
    status: str
    published_at: datetime | None
    is_demo: bool
    story_count: int = 0


class SearchResponse(BaseModel):
    query: str
    total: int
    items: list[StoryCard]
    mode: dict[str, Any] = Field(default_factory=dict)


class CategoryOut(BaseModel):
    slug: str
    label: str
    count: int


class AdminHealth(BaseModel):
    sources: list[SourceOut]
    latest_runs: list[dict[str, Any]]
    story_counts: dict[str, int]
    article_count: int
    cluster_count: int
    processing_mode: dict[str, Any] = Field(default_factory=dict)


class CapabilitiesOut(BaseModel):
    processing_mode: dict[str, Any]
    search: dict[str, Any]
    llm: dict[str, Any]
    embeddings: dict[str, Any]
