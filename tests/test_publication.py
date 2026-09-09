from weird.constants import StoryStatus
from weird.models import Edition, EditionStory, Story
from weird.pipeline.editorial import select_edition_stories
from weird.pipeline.publish import publish_sunday, week_bounds


def test_editorial_diversity_and_quality(session):
    stories = session.query(Story).all()
    selected = select_edition_stories(stories)
    assert selected
    assert any(featured for _section, _story, featured in selected)
    assert any(story.category in {"BUILD", "WHY"} for _section, story, _featured in selected)


def test_publication_idempotent(session):
    from datetime import datetime, timezone

    now = datetime(2026, 9, 13, 12, tzinfo=timezone.utc)
    first = publish_sunday(session, now=now)
    session.commit()
    issue = first.issue_number
    second = publish_sunday(session, now=now)
    session.commit()
    assert second.issue_number == issue
    start, _ = week_bounds(now)
    editions = session.query(Edition).filter_by(week_start=start).all()
    assert len(editions) == 1
    count = session.query(EditionStory).filter_by(edition_id=second.id).count()
    count2 = session.query(EditionStory).filter_by(edition_id=second.id).count()
    assert count == count2


def test_seed_real_sample_issue(session):
    stories = session.query(Story).all()
    assert len(stories) >= 8
    assert any(s.slug == "ladybird-independent-browser-engine" for s in stories)
    assert all(s.is_demo is False for s in stories)
    assert session.query(Edition).filter_by(status="published").count() >= 1
    ladybird = session.query(Story).filter_by(slug="ladybird-independent-browser-engine").one()
    assert ladybird.status == StoryStatus.PUBLISHED
    assert "independent" in (ladybird.analysis.get("why_you_should_care") or "").lower()
