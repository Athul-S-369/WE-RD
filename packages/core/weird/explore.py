from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from weird.config import get_settings
from weird.security import is_safe_http_url, sanitize_html

MAX_BYTES = 250_000
MAX_CHARS = 12_000


def explore_primary_url(url: str, *, max_chars: int = MAX_CHARS) -> dict[str, Any]:
    """Bounded primary-source exploration — fetch title/excerpt only, no unbounded crawl."""
    result: dict[str, Any] = {
        "url": url,
        "ok": False,
        "kind": "unknown",
        "title": "",
        "excerpt": "",
        "links": [],
        "error": None,
        "bounded": True,
    }
    if not url or not is_safe_http_url(url):
        result["error"] = "url_rejected"
        return result

    settings = get_settings()
    headers = {"User-Agent": "WE-RD/0.1 (+research; bounded)", "Accept": "text/html,text/plain,*/*"}
    try:
        with httpx.Client(timeout=min(settings.weird_http_timeout, 12.0), follow_redirects=True, headers=headers) as client:
            response = client.get(url)
            if response.status_code >= 400:
                result["error"] = f"http_{response.status_code}"
                return result
            content_type = (response.headers.get("content-type") or "").lower()
            raw = response.content[:MAX_BYTES]
            text = raw.decode(response.encoding or "utf-8", errors="replace")
    except httpx.HTTPError as exc:
        result["error"] = str(exc)[:240]
        return result

    host = urlparse(url).netloc.lower()
    if "github.com" in host:
        return _explore_githubish(url, text, content_type, max_chars)
    if "arxiv.org" in host:
        return _explore_html_doc(url, text, kind="paper", max_chars=max_chars)
    if "youtube.com" in host or "youtu.be" in host:
        result.update({"ok": True, "kind": "video_page", "title": _html_title(text) or url, "excerpt": ""})
        return result
    return _explore_html_doc(url, text, kind="article" if "html" in content_type else "text", max_chars=max_chars)


def _explore_githubish(url: str, text: str, content_type: str, max_chars: int) -> dict[str, Any]:
    # Prefer README-ish markdown bodies when present; else HTML.
    if "text/plain" in content_type or url.endswith(".md"):
        excerpt = sanitize_html(text)[:max_chars]
        return {
            "url": url,
            "ok": True,
            "kind": "readme",
            "title": url.rstrip("/").split("/")[-1],
            "excerpt": excerpt,
            "links": _extract_http_links(excerpt)[:12],
            "error": None,
            "bounded": True,
        }
    return _explore_html_doc(url, text, kind="repo_page", max_chars=max_chars)


def _explore_html_doc(url: str, html: str, *, kind: str, max_chars: int) -> dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    title = (soup.title.get_text(strip=True) if soup.title else "") or _html_title(html)
    article = soup.find("article") or soup.find("main") or soup.body
    text = article.get_text("\n", strip=True) if article else soup.get_text("\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    excerpt = sanitize_html(text)[:max_chars]
    links = []
    for a in (article or soup).find_all("a", href=True)[:40]:
        href = a["href"]
        if href.startswith("http") and is_safe_http_url(href):
            links.append({"url": href, "text": (a.get_text(" ", strip=True) or "")[:120]})
    return {
        "url": url,
        "ok": True,
        "kind": kind,
        "title": title[:512],
        "excerpt": excerpt,
        "links": links[:12],
        "error": None,
        "bounded": True,
    }


def _html_title(html: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html or "", flags=re.I | re.S)
    if not match:
        return ""
    return re.sub(r"\s+", " ", match.group(1)).strip()[:512]


def _extract_http_links(text: str) -> list[dict[str, str]]:
    found = re.findall(r"https?://[^\s)>\]]+", text or "")
    out = []
    for url in found:
        if is_safe_http_url(url):
            out.append({"url": url, "text": ""})
    return out


def explore_story_sources(sources: list[str], *, limit: int = 3) -> list[dict[str, Any]]:
    results = []
    for url in sources[:limit]:
        results.append(explore_primary_url(url))
    return results
