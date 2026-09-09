from datetime import datetime, timezone

from weird.dedup import is_duplicate
from weird.ingestion import NormalizedItem
from weird.models import Article, Story
from weird.pipeline.process import process_articles
from weird.textutil import canonicalize_url, content_hash
from weird.llm import get_provider


def test_mock_llm_does_not_invent_benchmarks():
    provider = get_provider()
    out = provider.complete_json("analyze", "Title: Demo\n", title="Demo", text="no numbers", category="BUILD")
    assert "do not establish" in out["performance"].lower() or "available sources" in out["performance"].lower()


def test_process_clusters_articles(session):
    now = datetime.now(timezone.utc)
    a = Article(
        title="Tiny OS in 400 lines of C",
        url="https://example.com/os-a",
        canonical_url=canonicalize_url("https://example.com/os-a"),
        content="kernel from scratch syscall allocator",
        summary="osdev",
        content_hash=content_hash("Tiny OS"),
        published_at=now,
        extra={},
    )
    b = Article(
        title="A tiny operating system in C",
        url="https://example.com/os-b",
        canonical_url=canonicalize_url("https://example.com/os-b"),
        content="kernel from scratch syscall allocator",
        summary="osdev",
        content_hash=content_hash("tiny operating"),
        published_at=now,
        extra={},
    )
    session.add_all([a, b])
    session.commit()
    metrics = process_articles(session)
    session.commit()
    assert metrics["clusters"] >= 1
    stories = session.query(Story).filter(Story.title.ilike("%tiny%")).all()
    assert stories


def test_normalized_item_shape():
    item = NormalizedItem(source_name="t", source_type="rss", title="x", url="https://example.com")
    assert item.title == "x"
    assert not is_duplicate(url=item.url, title=item.title, text="", existing=[])
