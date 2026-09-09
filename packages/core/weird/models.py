from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from weird.db import Base

JsonType = JSON().with_variant(JSONB, "postgresql")


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    credibility_score: Mapped[float] = mapped_column(Float, default=0.5)
    credibility_kind: Mapped[str] = mapped_column(String(64), default="community_post")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    extra: Mapped[dict[str, Any]] = mapped_column("metadata", JsonType, default=dict)
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    articles: Mapped[list[Article]] = relationship(back_populates="source")


class Article(Base):
    __tablename__ = "articles"
    __table_args__ = (UniqueConstraint("canonical_url", name="uq_articles_canonical_url"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"))
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    canonical_url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    author: Mapped[str | None] = mapped_column(String(255))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    content: Mapped[str] = mapped_column(Text, default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    embedding: Mapped[list[float] | None] = mapped_column(JsonType)
    extra: Mapped[dict[str, Any]] = mapped_column("metadata", JsonType, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source: Mapped[Source | None] = relationship(back_populates="articles")


class Story(Base):
    __tablename__ = "stories"
    __table_args__ = (UniqueConstraint("slug", name="uq_stories_slug"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    slug: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    dek: Mapped[str] = mapped_column(Text, default="")
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(32), index=True)
    signal_score: Mapped[float] = mapped_column(Float, default=0)
    cracked_score: Mapped[int] = mapped_column(Integer, default=0)
    rabbit_hole_score: Mapped[float] = mapped_column(Float, default=0)
    confidence: Mapped[str] = mapped_column(String(64), default="unverified")
    status: Mapped[str] = mapped_column(String(32), default="candidate", index=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    analysis: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict)
    security: Mapped[dict[str, Any] | None] = mapped_column(JsonType)
    leak: Mapped[dict[str, Any] | None] = mapped_column(JsonType)
    tags: Mapped[list[str]] = mapped_column(JsonType, default=list)
    cluster_key: Mapped[str | None] = mapped_column(String(256), index=True)
    extra: Mapped[dict[str, Any]] = mapped_column("metadata", JsonType, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    sources: Mapped[list[StorySource]] = relationship(back_populates="story", cascade="all, delete-orphan")
    timeline: Mapped[list[StoryTimeline]] = relationship(
        back_populates="story", cascade="all, delete-orphan", order_by="StoryTimeline.occurred_at"
    )
    videos: Mapped[list[Video]] = relationship(back_populates="story", cascade="all, delete-orphan")
    projects: Mapped[list[Project]] = relationship(back_populates="story", cascade="all, delete-orphan")


class StorySource(Base):
    __tablename__ = "story_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    story_id: Mapped[int] = mapped_column(ForeignKey("stories.id"), nullable=False)
    article_id: Mapped[int | None] = mapped_column(ForeignKey("articles.id"))
    role: Mapped[str] = mapped_column(String(64), default="supporting")
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[str] = mapped_column(String(512), default="")
    credibility_kind: Mapped[str] = mapped_column(String(64), default="secondary_reporting")
    credibility_score: Mapped[float] = mapped_column(Float, default=0.5)

    story: Mapped[Story] = relationship(back_populates="sources")
    article: Mapped[Article | None] = relationship()


class StoryTimeline(Base):
    __tablename__ = "story_timeline"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    story_id: Mapped[int] = mapped_column(ForeignKey("stories.id"), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    headline: Mapped[str] = mapped_column(String(512), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="")
    source_url: Mapped[str | None] = mapped_column(String(2048))

    story: Mapped[Story] = relationship(back_populates="timeline")


class Video(Base):
    __tablename__ = "videos"
    __table_args__ = (UniqueConstraint("story_id", "video_id", name="uq_videos_story_video"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    story_id: Mapped[int] = mapped_column(ForeignKey("stories.id"), nullable=False)
    video_id: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    channel: Mapped[str] = mapped_column(String(255), default="")
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    description: Mapped[str] = mapped_column(Text, default="")
    thumbnail: Mapped[str | None] = mapped_column(String(1024))
    relevance_score: Mapped[float] = mapped_column(Float, default=0)
    technical: Mapped[bool] = mapped_column(Boolean, default=True)

    story: Mapped[Story] = relationship(back_populates="videos")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    story_id: Mapped[int] = mapped_column(ForeignKey("stories.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    host: Mapped[str] = mapped_column(String(64), default="github")
    stars: Mapped[int | None] = mapped_column(Integer)
    language: Mapped[str | None] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(Text, default="")
    extra: Mapped[dict[str, Any]] = mapped_column("metadata", JsonType, default=dict)

    story: Mapped[Story] = relationship(back_populates="projects")


class Edition(Base):
    __tablename__ = "editions"
    __table_args__ = (
        UniqueConstraint("issue_number", name="uq_editions_issue_number"),
        UniqueConstraint("week_start", name="uq_editions_week_start"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    issue_number: Mapped[int] = mapped_column(Integer, nullable=False)
    week_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    week_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    masthead: Mapped[str] = mapped_column(String(255), default="The strange side of engineering.")
    week_in_numbers: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    stories: Mapped[list[EditionStory]] = relationship(
        back_populates="edition", cascade="all, delete-orphan", order_by="EditionStory.sort_order"
    )


class EditionStory(Base):
    __tablename__ = "edition_stories"
    __table_args__ = (UniqueConstraint("edition_id", "story_id", "section", name="uq_edition_story_section"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    edition_id: Mapped[int] = mapped_column(ForeignKey("editions.id"), nullable=False)
    story_id: Mapped[int] = mapped_column(ForeignKey("stories.id"), nullable=False)
    section: Mapped[str] = mapped_column(String(128), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    featured: Mapped[bool] = mapped_column(Boolean, default=False)

    edition: Mapped[Edition] = relationship(back_populates="stories")
    story: Mapped[Story] = relationship()


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default="running")
    metrics: Mapped[dict[str, Any]] = mapped_column(JsonType, default=dict)
    error: Mapped[str | None] = mapped_column(Text)


class LlmCache(Base):
    __tablename__ = "llm_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cache_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    prompt_name: Mapped[str] = mapped_column(String(128), nullable=False)
    response: Mapped[dict[str, Any]] = mapped_column(JsonType, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
