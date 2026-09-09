from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from weird.constants import EditionStatus, StoryStatus
from weird.models import Article, Edition, EditionStory, PipelineRun, Story
from weird.pipeline.editorial import select_edition_stories


def week_bounds(now: datetime | None = None) -> tuple[datetime, datetime]:
    now = now or datetime.now(timezone.utc)
    # ISO week: Monday 00:00 to Sunday 23:59
    monday = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    sunday = monday + timedelta(days=6, hours=23, minutes=59)
    return monday, sunday


def collect_week_metrics(session: Session) -> dict[str, int]:
    """Real counts from the database — never fabricated marketing numbers."""
    latest = (
        session.query(PipelineRun)
        .filter(PipelineRun.kind == "daily", PipelineRun.status == "ok")
        .order_by(PipelineRun.finished_at.desc())
        .first()
    )
    fetched = int((latest.metrics or {}).get("fetched", 0)) if latest else 0
    return {
        "sources_scanned": max(_source_count(session), fetched),
        "candidate_stories": session.query(Article).count(),
        "story_clusters": session.query(Story).count(),
        "high_signal_stories": session.query(Story).filter(Story.signal_score >= 70).count(),
        "published": session.query(Story).filter_by(status=StoryStatus.PUBLISHED).count(),
        "rabbit_holes_discovered": session.query(Story).filter(Story.rabbit_hole_score >= 70).count(),
        "extremely_cracked": session.query(Story).filter(Story.cracked_score >= 90).count(),
    }


def _source_count(session: Session) -> int:
    from weird.models import Source

    return session.query(Source).count()


def publish_sunday(session: Session, now: datetime | None = None) -> Edition:
    now = now or datetime.now(timezone.utc)
    week_start, week_end = week_bounds(now)
    existing = session.query(Edition).filter_by(week_start=week_start).one_or_none()
    if existing and existing.status == EditionStatus.PUBLISHED:
        return existing

    candidates = (
        session.query(Story)
        .filter(Story.status.in_([StoryStatus.ANALYZED, StoryStatus.SELECTED, StoryStatus.PUBLISHED, StoryStatus.CLUSTERED]))
        .all()
    )
    live = [s for s in candidates if not s.is_demo] or candidates
    assignments = select_edition_stories(live)
    metrics = collect_week_metrics(session)
    metrics["published"] = len({s.id for _, s, _ in assignments})

    if existing is None:
        last = session.query(Edition).order_by(Edition.issue_number.desc()).first()
        issue = (last.issue_number + 1) if last else 1
        edition = Edition(
            issue_number=issue,
            week_start=week_start,
            week_end=week_end,
            status=EditionStatus.DRAFT,
            masthead="The strange side of engineering.",
            week_in_numbers=metrics,
            is_demo=all(s.is_demo for _, s, _ in assignments) if assignments else False,
        )
        session.add(edition)
        session.flush()
    else:
        edition = existing
        edition.week_in_numbers = metrics
        session.query(EditionStory).filter_by(edition_id=edition.id).delete()

    for index, (section, story, featured) in enumerate(assignments):
        session.add(
            EditionStory(
                edition_id=edition.id,
                story_id=story.id,
                section=section,
                sort_order=index,
                featured=featured,
            )
        )
        story.status = StoryStatus.PUBLISHED
    edition.status = EditionStatus.PUBLISHED
    edition.published_at = now
    session.flush()
    return edition


def start_run(session: Session, kind: str) -> PipelineRun:
    run = PipelineRun(kind=kind, status="running", metrics={})
    session.add(run)
    session.flush()
    return run


def finish_run(session: Session, run: PipelineRun, metrics: dict, error: str | None = None) -> None:
    run.finished_at = datetime.now(timezone.utc)
    run.metrics = metrics
    run.status = "failed" if error else "ok"
    run.error = error
    session.flush()
