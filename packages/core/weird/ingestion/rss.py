from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import feedparser
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from weird.config import get_settings
from weird.ingestion import NormalizedItem
from weird.ingestion.base import SourceAdapter


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (TypeError, ValueError):
        return None


class RssAdapter(SourceAdapter):
    source_type = "rss"

    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3), reraise=True)
    def fetch(self) -> list[NormalizedItem]:
        timeout = get_settings().weird_http_timeout
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(self.url, headers={"User-Agent": "WE-RD/0.1 (+https://github.com)"})
            response.raise_for_status()
            parsed = feedparser.parse(response.content)
        items: list[NormalizedItem] = []
        for entry in parsed.entries:
            link = entry.get("link") or ""
            title = entry.get("title") or ""
            if not link or not title:
                continue
            summary = entry.get("summary") or entry.get("description") or ""
            content = ""
            if entry.get("content"):
                content = entry.content[0].get("value") or ""
            published = _parse_date(entry.get("published") or entry.get("updated"))
            items.append(
                NormalizedItem(
                    source_name=self.name,
                    source_type="rss",
                    title=title.strip(),
                    url=link.strip(),
                    author=(entry.get("author") or None),
                    published_at=published,
                    content=content,
                    summary=summary,
                    extra={"feed": self.url},
                )
            )
        return items
