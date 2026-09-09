from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from weird.analysis_fallback import editorial_heuristic
from weird.config import get_settings
from weird.constants import StoryStatus
from weird.enrichment.github import fetch_repo, github_repo_from_url, parse_github_urls_from_text
from weird.enrichment.youtube import YouTubeClient, search_queries_for_story
from weird.explore import explore_primary_url
from weird.llm import get_provider, provider_status
from weird.llm.prompts import render_prompt
from weird.models import LlmCache, Project, Story, StorySource, Video
from weird.scoring import extract_tags


def _cache_get(session: Session, key: str) -> dict[str, Any] | None:
    row = session.query(LlmCache).filter_by(cache_key=key).one_or_none()
    return row.response if row else None


def _cache_put(session: Session, key: str, provider: str, prompt_name: str, response: dict[str, Any]) -> None:
    session.add(LlmCache(cache_key=key, provider=provider, prompt_name=prompt_name, response=response))


def analyze_top_stories(session: Session) -> dict[str, int]:
    settings = get_settings()
    provider = get_provider(settings)
    status = provider_status(settings)
    stories = (
        session.query(Story)
        .filter(Story.status.in_([StoryStatus.CLUSTERED, StoryStatus.ANALYZED, StoryStatus.CANDIDATE]))
        .order_by(Story.signal_score.desc())
        .limit(settings.weird_max_llm_candidates)
        .all()
    )
    analyzed = 0
    for story in stories:
        sources = session.query(StorySource).filter_by(story_id=story.id).all()
        source_blob = "\n".join(f"- {s.title} ({s.url})" for s in sources)
        text = f"{story.title}\n{story.description}\n{source_blob}"

        # Bounded primary-source exploration (optional, network).
        explorations: list[dict[str, Any]] = []
        if settings.weird_explore_sources:
            for src in sources[: settings.weird_explore_max_per_story]:
                try:
                    explorations.append(explore_primary_url(src.url))
                except Exception:  # noqa: BLE001
                    continue
            evidence_bits = "\n".join(
                f"{e.get('title','')}: {str(e.get('excerpt',''))[:800]}" for e in explorations if e.get("ok")
            )
            if evidence_bits:
                text = f"{text}\n\nPRIMARY EXCERPTS:\n{evidence_bits}"

        cache_key = hashlib.sha256(f"{provider.name}:analyze:{story.slug}:{text[:1500]}".encode()).hexdigest()
        cached = _cache_get(session, cache_key)
        if cached:
            analysis = cached
        else:
            facts = provider.complete_json(
                "facts",
                render_prompt("facts", title=story.title, sources=source_blob or story.description),
                title=story.title,
                text=text,
            )
            analysis = provider.complete_json(
                "analyze",
                render_prompt(
                    "analyze",
                    title=story.title,
                    category=story.category,
                    facts=json.dumps(facts),
                    text=text[:4000],
                ),
                title=story.title,
                text=text,
                category=story.category,
                sources=source_blob,
            )
            validated = provider.complete_json(
                "validate",
                render_prompt("validate", draft=json.dumps(analysis), facts=json.dumps(facts)),
            )
            if validated.get("rewrites"):
                analysis.update(validated["rewrites"])
            analysis["facts"] = facts
            analysis["generation_mode"] = analysis.get("generation_mode") or status["mode_label"]
            analysis["provider"] = provider.name
            if explorations:
                analysis["explorations"] = [
                    {"url": e.get("url"), "ok": e.get("ok"), "kind": e.get("kind"), "title": e.get("title")}
                    for e in explorations
                ]
            _cache_put(session, cache_key, provider.name, "analyze", analysis)

        editorial = provider.complete_json(
            "editorial",
            render_prompt(
                "editorial",
                title=story.title,
                category=story.category,
                signal=str(story.signal_score),
                cracked=str(story.cracked_score),
                rabbit=str(story.rabbit_hole_score),
                confidence=story.confidence,
                tags=", ".join(story.tags or []),
                has_primary=str(bool((analysis.get("evidence") or {}).get("has_primary_source"))),
                excerpt=str(analysis.get("quick_read") or analysis.get("what_happened") or "")[:500],
            ),
            title=story.title,
            category=story.category,
            signal_score=story.signal_score,
            cracked_score=story.cracked_score,
            rabbit_hole_score=story.rabbit_hole_score,
            confidence=story.confidence,
            evidence=analysis.get("evidence") or {},
        )
        if not isinstance(editorial, dict) or "keep" not in editorial:
            editorial = editorial_heuristic(
                {
                    "signal_score": story.signal_score,
                    "cracked_score": story.cracked_score,
                    "rabbit_hole_score": story.rabbit_hole_score,
                    "confidence": story.confidence,
                    "category": story.category,
                    "evidence": analysis.get("evidence") or {},
                }
            )

        story.analysis = analysis
        story.extra = {
            **(story.extra or {}),
            "editorial": editorial,
            "processing_mode": status["mode_label"],
            "provider": provider.name,
        }
        if not story.tags:
            story.tags = extract_tags(text)
        story.status = StoryStatus.ANALYZED
        analyzed += 1
    session.flush()
    return {"analyzed": analyzed, "provider": provider.name, "mode": status["mode_label"]}


def enrich_stories(session: Session) -> dict[str, int | str]:
    yt = YouTubeClient()
    stories = (
        session.query(Story)
        .filter(Story.status.in_([StoryStatus.ANALYZED, StoryStatus.SELECTED, StoryStatus.PUBLISHED]))
        .all()
    )
    videos_added = 0
    projects_added = 0
    no_video = 0
    for story in stories:
        sources = session.query(StorySource).filter_by(story_id=story.id).all()
        existing_projects = {p.url for p in story.projects}
        repo_names = []
        for source in sources:
            repo = github_repo_from_url(source.url)
            if repo:
                repo_names.append(repo)
        # Also mine description/analysis for github URLs.
        blob = f"{story.description}\n{json.dumps(story.analysis or {})}"
        repo_names.extend(parse_github_urls_from_text(blob))
        seen_repos: set[str] = set()
        for repo in repo_names:
            if repo in seen_repos:
                continue
            seen_repos.add(repo)
            info = fetch_repo(repo) or {
                "name": repo,
                "url": f"https://github.com/{repo}",
                "stars": None,
                "language": None,
                "description": "",
                "topics": [],
            }
            project_url = info.get("url") or f"https://github.com/{repo}"
            if project_url in existing_projects:
                continue
            session.add(
                Project(
                    story_id=story.id,
                    name=info.get("name") or repo,
                    url=project_url,
                    host="github",
                    stars=info.get("stars"),
                    language=info.get("language"),
                    description=info.get("description") or "",
                    extra={
                        "topics": info.get("topics") or [],
                        "languages": info.get("languages") or {},
                        "license": info.get("license"),
                        "readme_excerpt": (info.get("readme_excerpt") or "")[:1500],
                        "forks": info.get("forks"),
                        "enriched_with_token": info.get("enriched_with_token", False),
                    },
                )
            )
            existing_projects.add(info["url"])
            projects_added += 1

        existing_vids = {v.video_id for v in story.videos}
        queries = search_queries_for_story(
            story.title, story.tags or [], (story.extra or {}).get("rabbit_paths") or []
        )
        status_payload = yt.search_with_status(queries)
        story.extra = {
            **(story.extra or {}),
            "youtube_status": status_payload.get("status"),
            "youtube_provider": status_payload.get("provider"),
        }
        found = status_payload.get("results") or []
        if status_payload.get("status") == "NO VIDEO FOUND":
            no_video += 1
        for item in found:
            if item["video_id"] in existing_vids:
                continue
            published = None
            if item.get("published_at"):
                try:
                    published = datetime.fromisoformat(str(item["published_at"]).replace("Z", "+00:00"))
                    if published.tzinfo is None:
                        published = published.replace(tzinfo=timezone.utc)
                except ValueError:
                    published = None
            session.add(
                Video(
                    story_id=story.id,
                    video_id=item["video_id"],
                    title=item["title"],
                    channel=item.get("channel") or "",
                    url=item["url"],
                    description=item.get("description") or "",
                    thumbnail=item.get("thumbnail"),
                    published_at=published,
                    relevance_score=item.get("relevance_score") or 0,
                    technical=item.get("technical", True),
                )
            )
            existing_vids.add(item["video_id"])
            videos_added += 1
    session.flush()
    return {
        "videos": videos_added,
        "projects": projects_added,
        "youtube_no_video": no_video,
        "youtube_provider": yt.provider.name,
    }
