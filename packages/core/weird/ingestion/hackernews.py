from __future__ import annotations

from datetime import datetime, timezone

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from weird.config import get_settings
from weird.ingestion import NormalizedItem
from weird.ingestion.base import SourceAdapter

HN_TOP = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM = "https://hacker-news.firebaseio.com/v0/item/{id}.json"


class HackerNewsAdapter(SourceAdapter):
    name = "Hacker News"
    source_type = "hn"

    def __init__(self, limit: int = 60):
        self.limit = limit

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3), reraise=True)
    def fetch(self) -> list[NormalizedItem]:
        timeout = get_settings().weird_http_timeout
        items: list[NormalizedItem] = []
        with httpx.Client(timeout=timeout) as client:
            ids = client.get(HN_TOP).json()[: self.limit]
            for story_id in ids:
                try:
                    data = client.get(HN_ITEM.format(id=story_id)).json()
                except Exception:
                    continue
                if not data or data.get("type") != "story":
                    continue
                url = data.get("url") or f"https://news.ycombinator.com/item?id={story_id}"
                ts = data.get("time")
                published = datetime.fromtimestamp(ts, tz=timezone.utc) if ts else None
                items.append(
                    NormalizedItem(
                        source_name=self.name,
                        source_type="hn",
                        title=data.get("title") or "",
                        url=url,
                        author=data.get("by"),
                        published_at=published,
                        content=data.get("text") or "",
                        summary="",
                        extra={
                            "hn_id": story_id,
                            "score": data.get("score"),
                            "comments": data.get("descendants"),
                        },
                    )
                )
        return [i for i in items if i.title]
