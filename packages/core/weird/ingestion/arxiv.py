from __future__ import annotations

from datetime import datetime, timezone

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from weird.config import get_settings
from weird.ingestion import NormalizedItem
from weird.ingestion.base import SourceAdapter

ARXIV_API = "https://export.arxiv.org/api/query"


class ArxivAdapter(SourceAdapter):
    name = "arXiv"
    source_type = "arxiv"

    def __init__(self, search: str = "cat:cs.OS OR cat:cs.PL OR cat:cs.CR OR cat:cs.DC OR cat:cs.AR"):
        self.search = search

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3), reraise=True)
    def fetch(self) -> list[NormalizedItem]:
        timeout = get_settings().weird_http_timeout
        params = {"search_query": self.search, "start": 0, "max_results": 40, "sortBy": "submittedDate"}
        with httpx.Client(timeout=timeout) as client:
            xml = client.get(ARXIV_API, params=params).text
        import feedparser

        parsed = feedparser.parse(xml)
        items: list[NormalizedItem] = []
        for entry in parsed.entries:
            published = None
            if entry.get("published"):
                published = datetime.fromisoformat(entry.published.replace("Z", "+00:00"))
                if published.tzinfo is None:
                    published = published.replace(tzinfo=timezone.utc)
            items.append(
                NormalizedItem(
                    source_name=self.name,
                    source_type="arxiv",
                    title=(entry.get("title") or "").replace("\n", " ").strip(),
                    url=entry.get("link") or "",
                    author=", ".join(a.get("name", "") for a in entry.get("authors", [])[:4]),
                    published_at=published,
                    content=(entry.get("summary") or "").strip(),
                    extra={"arxiv": True},
                )
            )
        return [i for i in items if i.title and i.url]
