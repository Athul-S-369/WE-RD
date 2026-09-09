from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from weird.config import get_settings


class YouTubeProvider(ABC):
    name: str

    @abstractmethod
    def search(self, queries: list[str], max_results: int = 5) -> list[dict[str, Any]]:
        raise NotImplementedError


class NoKeyYouTubeProvider(YouTubeProvider):
    """Honest zero-key provider: never fabricates video IDs."""

    name = "none"

    def search(self, queries: list[str], max_results: int = 5) -> list[dict[str, Any]]:
        return []


class ApiYouTubeProvider(YouTubeProvider):
    name = "youtube_data_api"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.settings = get_settings()

    def search(self, queries: list[str], max_results: int = 5) -> list[dict[str, Any]]:
        found: list[dict[str, Any]] = []
        for query in queries[:4]:
            found.extend(self._api_search(query, max_results=max_results))
        deduped: dict[str, dict[str, Any]] = {}
        for item in found:
            deduped[item["video_id"]] = item
        return sorted(deduped.values(), key=lambda x: x.get("relevance_score", 0), reverse=True)[:max_results]

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3), reraise=True)
    def _api_search(self, query: str, max_results: int) -> list[dict[str, Any]]:
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max_results,
            "key": self.api_key,
            "videoEmbeddable": "true",
            "relevanceLanguage": "en",
        }
        with httpx.Client(timeout=self.settings.weird_http_timeout) as client:
            data = client.get("https://www.googleapis.com/youtube/v3/search", params=params).json()
        results = []
        for item in data.get("items", []):
            vid = (item.get("id") or {}).get("videoId")
            snippet = item.get("snippet") or {}
            if not vid:
                continue
            title = snippet.get("title") or ""
            channel = snippet.get("channelTitle") or ""
            technical = is_technical_video(title, snippet.get("description") or "", channel)
            results.append(
                {
                    "video_id": vid,
                    "title": title,
                    "channel": channel,
                    "url": f"https://www.youtube.com/watch?v={vid}",
                    "description": snippet.get("description") or "",
                    "thumbnail": ((snippet.get("thumbnails") or {}).get("high") or {}).get("url"),
                    "published_at": snippet.get("publishedAt"),
                    "relevance_score": 0.7 if technical else 0.3,
                    "technical": technical,
                    "provider": self.name,
                }
            )
        return results


class YouTubeClient:
    def __init__(self, provider: YouTubeProvider | None = None) -> None:
        self.settings = get_settings()
        self.provider = provider or get_youtube_provider()

    def search(self, queries: list[str], max_results: int = 5) -> list[dict[str, Any]]:
        return self.provider.search(queries, max_results=max_results)

    def search_with_status(self, queries: list[str], max_results: int = 5) -> dict[str, Any]:
        try:
            results = self.search(queries, max_results=max_results)
        except Exception as exc:  # noqa: BLE001
            return {
                "status": "ERROR",
                "message": str(exc)[:240],
                "provider": self.provider.name,
                "results": [],
            }
        if not results:
            return {
                "status": "NO VIDEO FOUND",
                "message": "No technical videos matched (API empty or no key configured).",
                "provider": self.provider.name,
                "results": [],
            }
        return {"status": "OK", "message": "", "provider": self.provider.name, "results": results}


def get_youtube_provider() -> YouTubeProvider:
    settings = get_settings()
    if settings.youtube_api_key:
        return ApiYouTubeProvider(settings.youtube_api_key)
    return NoKeyYouTubeProvider()


def is_technical_video(title: str, description: str, channel: str) -> bool:
    blob = f"{title} {description} {channel}".lower()
    needles = [
        "talk",
        "conference",
        "impl",
        "compiler",
        "kernel",
        "deep dive",
        "architecture",
        "research",
        "defcon",
        "usenix",
        "cppcon",
        "rustconf",
        "fosdem",
        "lecture",
    ]
    reactions = ["reacts to", "reaction", "clicked", "you won't believe"]
    if any(n in blob for n in reactions):
        return False
    return any(n in blob for n in needles)


def search_queries_for_story(title: str, tags: list[str], entities: list[str]) -> list[str]:
    queries = [
        f"{title} engineering talk",
        f"{title} implementation",
        f"{' '.join(tags[:3])} conference talk",
        f"{' '.join(entities[:3])} architecture deep dive",
    ]
    return [q.strip() for q in queries if q.strip()]
