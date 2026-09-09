from __future__ import annotations

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from weird.config import get_settings
from weird.ingestion import NormalizedItem
from weird.ingestion.base import SourceAdapter

TRENDING = "https://github.com/trending"


class GithubTrendingAdapter(SourceAdapter):
    name = "GitHub Trending"
    source_type = "github"

    def __init__(self, language: str = ""):
        self.language = language

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3), reraise=True)
    def fetch(self) -> list[NormalizedItem]:
        settings = get_settings()
        headers = {"User-Agent": "WE-RD/0.1", "Accept": "application/vnd.github+json"}
        if settings.github_token:
            headers["Authorization"] = f"Bearer {settings.github_token}"
            # Official search API — not HTML scraping.
            q = "created:>2024-01-01 stars:>20"
            if self.language:
                q += f" language:{self.language}"
            with httpx.Client(timeout=settings.weird_http_timeout, headers=headers) as client:
                data = client.get(
                    "https://api.github.com/search/repositories",
                    params={"q": q, "sort": "updated", "order": "desc", "per_page": 25},
                ).json()
            items = []
            for repo in data.get("items", []):
                items.append(
                    NormalizedItem(
                        source_name=self.name,
                        source_type="github",
                        title=repo.get("full_name") or "",
                        url=repo.get("html_url") or "",
                        author=(repo.get("owner") or {}).get("login"),
                        content=repo.get("description") or "",
                        extra={
                            "stars": repo.get("stargazers_count"),
                            "language": repo.get("language"),
                        },
                    )
                )
            return [i for i in items if i.title]
        # Without a token, skip network trending to avoid brittle HTML scraping.
        return []
