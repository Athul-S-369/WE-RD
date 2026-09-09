from __future__ import annotations

from datetime import datetime, timezone

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from weird.config import get_settings
from weird.ingestion import NormalizedItem
from weird.ingestion.base import SourceAdapter

LOBSTERS = "https://lobste.rs/hottest.json"


class LobstersAdapter(SourceAdapter):
    name = "Lobsters"
    source_type = "lobsters"

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3), reraise=True)
    def fetch(self) -> list[NormalizedItem]:
        timeout = get_settings().weird_http_timeout
        with httpx.Client(timeout=timeout, headers={"User-Agent": "WE-RD/0.1"}) as client:
            rows = client.get(LOBSTERS).json()
        items: list[NormalizedItem] = []
        for row in rows:
            created = row.get("created_at")
            published = None
            if created:
                published = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if published.tzinfo is None:
                    published = published.replace(tzinfo=timezone.utc)
            items.append(
                NormalizedItem(
                    source_name=self.name,
                    source_type="lobsters",
                    title=row.get("title") or "",
                    url=row.get("url") or row.get("short_id_url") or "",
                    author=(row.get("submitter_user") or {}).get("username"),
                    published_at=published,
                    content=row.get("description") or "",
                    extra={
                        "score": row.get("score"),
                        "comments": row.get("comment_count"),
                        "tags": row.get("tags"),
                    },
                )
            )
        return [i for i in items if i.title and i.url]
