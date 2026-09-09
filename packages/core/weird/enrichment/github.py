from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import httpx

from weird.config import get_settings


def github_repo_from_url(url: str) -> str | None:
    parsed = urlparse(url)
    if "github.com" not in parsed.netloc.lower():
        return None
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        return None
    return f"{parts[0]}/{parts[1].removesuffix('.git')}"


def _headers() -> dict[str, str]:
    settings = get_settings()
    headers = {
        "User-Agent": "WE-RD/0.1",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    return headers


def fetch_repo(full_name: str) -> dict[str, Any] | None:
    """Enrich a GitHub repo. Works without a token (rate-limited); richer with a token."""
    settings = get_settings()
    try:
        with httpx.Client(timeout=settings.weird_http_timeout, headers=_headers()) as client:
            response = client.get(f"https://api.github.com/repos/{full_name}")
            if response.status_code >= 400:
                return None
            data = response.json()
            languages: dict[str, int] = {}
            readme_excerpt = ""
            license_spdx = ((data.get("license") or {}) or {}).get("spdx_id")
            # Best-effort extras — never fail the whole enrichment.
            try:
                lang_resp = client.get(f"https://api.github.com/repos/{full_name}/languages")
                if lang_resp.status_code < 400:
                    languages = lang_resp.json() or {}
            except httpx.HTTPError:
                languages = {}
            try:
                readme_resp = client.get(
                    f"https://api.github.com/repos/{full_name}/readme",
                    headers={**_headers(), "Accept": "application/vnd.github.raw"},
                )
                if readme_resp.status_code < 400:
                    readme_excerpt = readme_resp.text[:4000]
            except httpx.HTTPError:
                readme_excerpt = ""
    except httpx.HTTPError:
        return None
    return {
        "name": data.get("full_name") or full_name,
        "url": data.get("html_url") or f"https://github.com/{full_name}",
        "stars": data.get("stargazers_count"),
        "forks": data.get("forks_count"),
        "open_issues": data.get("open_issues_count"),
        "language": data.get("language"),
        "languages": languages if isinstance(languages, dict) and "message" not in languages else {},
        "description": data.get("description") or "",
        "topics": data.get("topics") or [],
        "license": license_spdx,
        "default_branch": data.get("default_branch"),
        "archived": bool(data.get("archived")),
        "readme_excerpt": readme_excerpt,
        "enriched_with_token": bool(settings.github_token),
    }


def parse_github_urls_from_text(text: str) -> list[str]:
    found = []
    for token in (text or "").split():
        if "github.com/" in token.lower():
            cleaned = token.strip("()[]<>,.\"'")
            repo = github_repo_from_url(cleaned if "://" in cleaned else f"https://{cleaned}")
            if repo:
                found.append(repo)
    # preserve order, unique
    out: list[str] = []
    for repo in found:
        if repo not in out:
            out.append(repo)
    return out[:8]
