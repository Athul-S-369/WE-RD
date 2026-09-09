from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session, joinedload

from weird.constants import EditionStatus
from weird.db import get_session_factory, init_db
from weird.graph import build_source_graph
from weird.logging import configure_logging, get_logger
from weird.models import Edition, EditionStory, Story
from weird.serializers import to_card, to_detail, to_edition, to_edition_list_item

log = get_logger("export_site")

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_CONTENT_DIR = REPO_ROOT / "apps" / "web" / "public" / "content"
DEFAULT_DATA_DIR = REPO_ROOT / "data"


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def export_static_site(session: Session, content_dir: Path | None = None) -> dict[str, int]:
    """Dump published newspaper JSON for GitHub Pages / static Next export."""
    out = content_dir or DEFAULT_CONTENT_DIR
    out.mkdir(parents=True, exist_ok=True)

    editions = (
        session.query(Edition)
        .options(joinedload(Edition.stories).joinedload(EditionStory.story).joinedload(Story.sources))
        .filter(Edition.status == EditionStatus.PUBLISHED)
        .order_by(Edition.issue_number.desc())
        .all()
    )

    edition_list = [to_edition_list_item(e).model_dump(mode="json") for e in editions]
    _write(out / "editions.json", edition_list)

    current = editions[0] if editions else None
    if current:
        current_payload = to_edition(current).model_dump(mode="json")
        _write(out / "current.json", current_payload)
        _write(out / "editions" / f"{current.issue_number}.json", current_payload)
    else:
        _write(out / "current.json", None)

    for edition in editions[1:]:
        # Reload with relationships for each (list query already loaded)
        payload = to_edition(edition).model_dump(mode="json")
        _write(out / "editions" / f"{edition.issue_number}.json", payload)

    stories = (
        session.query(Story)
        .options(
            joinedload(Story.sources),
            joinedload(Story.timeline),
            joinedload(Story.videos),
            joinedload(Story.projects),
        )
        .order_by(Story.signal_score.desc())
        .all()
    )

    cards = []
    for story in stories:
        graph = build_source_graph(session, story)
        detail = to_detail(
            story,
            related=graph.related,
            source_graph={
                "nodes": [
                    {"kind": n.kind, "id": n.id, "label": n.label, "url": n.url}
                    for n in graph.nodes
                ],
                "edges": [
                    {"source": e.source, "target": e.target, "relation": e.relation}
                    for e in graph.edges
                ],
            },
        )
        detail_dict = detail.model_dump(mode="json")
        _write(out / "stories" / f"{story.slug}.json", detail_dict)
        cards.append(to_card(story).model_dump(mode="json"))

    _write(out / "stories-index.json", cards)

    by_cat: dict[str, list] = {}
    for card in cards:
        by_cat.setdefault(card["category"], []).append(card)
    _write(out / "categories.json", by_cat)

    meta = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "edition_count": len(editions),
        "story_count": len(stories),
        "current_issue": current.issue_number if current else None,
        "publisher": "github-pages",
    }
    _write(out / "meta.json", meta)

    data_dir = DEFAULT_DATA_DIR
    data_dir.mkdir(parents=True, exist_ok=True)
    _write(data_dir / "last-export.json", meta)

    log.info("export_site_ok", editions=len(editions), stories=len(stories), path=str(out))
    return {"editions": len(editions), "stories": len(stories)}


def main() -> None:
    configure_logging()
    init_db()
    session = get_session_factory()()
    try:
        from weird.config import get_settings
        from weird.seed import seed

        if get_settings().weird_demo_mode and session.query(Story).count() == 0:
            seed(session)
            session.commit()
        export_static_site(session)
        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    main()
