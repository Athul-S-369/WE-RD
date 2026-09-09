from __future__ import annotations

from weird.db import get_session_factory, init_db
from weird.logging import configure_logging, get_logger
from weird.pipeline.analyze import analyze_top_stories, enrich_stories
from weird.pipeline.ingest import ingest_all
from weird.pipeline.process import process_articles
from weird.pipeline.publish import finish_run, start_run

log = get_logger("daily")


def run_daily() -> dict:
    configure_logging()
    init_db()
    session = get_session_factory()()
    run = start_run(session, "daily")
    metrics: dict = {}
    try:
        metrics["ingest"] = ingest_all(session)
        metrics["process"] = process_articles(session)
        metrics["analyze"] = analyze_top_stories(session)
        metrics["enrich"] = enrich_stories(session)
        finish_run(session, run, metrics)
        session.commit()

        # Persist a small JSON breadcrumb for GitHub corpus history.
        from datetime import datetime, timezone
        from pathlib import Path
        import json

        data_dir = Path(__file__).resolve().parents[4] / "data" / "pipeline"
        data_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        (data_dir / f"daily-{stamp}.json").write_text(
            json.dumps({"at": datetime.now(timezone.utc).isoformat(), "metrics": metrics}, indent=2, default=str),
            encoding="utf-8",
        )
        log.info("daily_ok", **{k: str(v)[:200] for k, v in metrics.items()})
        return metrics
    except Exception as exc:
        session.rollback()
        session2 = get_session_factory()()
        try:
            finish_run(session2, session2.merge(run), metrics, error=str(exc))
            session2.commit()
        finally:
            session2.close()
        log.error("daily_failed", error=str(exc))
        raise
    finally:
        session.close()


def main() -> None:
    run_daily()


if __name__ == "__main__":
    main()
