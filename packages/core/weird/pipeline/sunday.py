from __future__ import annotations

from weird.db import get_session_factory, init_db
from weird.logging import configure_logging, get_logger
from weird.pipeline.analyze import analyze_top_stories, enrich_stories
from weird.pipeline.export_site import export_static_site
from weird.pipeline.publish import finish_run, publish_sunday, start_run

log = get_logger("sunday")


def run_sunday() -> dict:
    configure_logging()
    init_db()
    session = get_session_factory()()
    run = start_run(session, "sunday")
    metrics: dict = {}
    try:
        metrics["analyze"] = analyze_top_stories(session)
        metrics["enrich"] = enrich_stories(session)
        edition = publish_sunday(session)
        metrics["issue_number"] = edition.issue_number
        metrics["week_in_numbers"] = edition.week_in_numbers
        metrics["export"] = export_static_site(session)
        finish_run(session, run, metrics)
        session.commit()
        log.info("sunday_ok", issue=edition.issue_number)
        return metrics
    except Exception as exc:
        session.rollback()
        session2 = get_session_factory()()
        try:
            finish_run(session2, session2.merge(run), metrics, error=str(exc))
            session2.commit()
        finally:
            session2.close()
        log.error("sunday_failed", error=str(exc))
        raise
    finally:
        session.close()


def main() -> None:
    run_sunday()


if __name__ == "__main__":
    main()
