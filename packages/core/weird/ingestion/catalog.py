from __future__ import annotations

from dataclasses import dataclass

from weird.constants import CredibilityKind
from weird.ingestion.arxiv import ArxivAdapter
from weird.ingestion.base import SourceAdapter
from weird.ingestion.cve import CveAdapter
from weird.ingestion.github import GithubTrendingAdapter
from weird.ingestion.hackernews import HackerNewsAdapter
from weird.ingestion.lobsters import LobstersAdapter
from weird.ingestion.rss import RssAdapter


@dataclass
class SourceSpec:
    name: str
    type: str
    url: str
    credibility_score: float
    credibility_kind: str
    factory: type[SourceAdapter] | None = None
    kwargs: dict | None = None


DEFAULT_SOURCES: list[SourceSpec] = [
    SourceSpec(
        "Hacker News",
        "hn",
        "https://news.ycombinator.com",
        0.62,
        CredibilityKind.COMMUNITY,
        HackerNewsAdapter,
    ),
    SourceSpec(
        "Lobsters",
        "lobsters",
        "https://lobste.rs",
        0.72,
        CredibilityKind.COMMUNITY,
        LobstersAdapter,
    ),
    SourceSpec(
        "arXiv",
        "arxiv",
        "https://arxiv.org",
        0.9,
        CredibilityKind.RESEARCH_PAPER,
        ArxivAdapter,
    ),
    SourceSpec(
        "NVD CVE",
        "cve",
        "https://nvd.nist.gov",
        0.95,
        CredibilityKind.VENDOR_ADVISORY,
        CveAdapter,
    ),
    SourceSpec(
        "GitHub Trending",
        "github",
        "https://github.com",
        0.8,
        CredibilityKind.OFFICIAL_REPO,
        GithubTrendingAdapter,
    ),
    SourceSpec(
        "LWN",
        "rss",
        "https://lwn.net/headlines/rss",
        0.88,
        CredibilityKind.RESPECTED_PUBLICATION,
        RssAdapter,
        {"name": "LWN", "url": "https://lwn.net/headlines/rss"},
    ),
    SourceSpec(
        "Phoronix",
        "rss",
        "https://www.phoronix.com/rss.php",
        0.7,
        CredibilityKind.RESPECTED_PUBLICATION,
        RssAdapter,
        {"name": "Phoronix", "url": "https://www.phoronix.com/rss.php"},
    ),
    SourceSpec(
        "USENIX",
        "rss",
        "https://www.usenix.org/rss.xml",
        0.9,
        CredibilityKind.ACADEMIC,
        RssAdapter,
        {"name": "USENIX", "url": "https://www.usenix.org/rss.xml"},
    ),
    SourceSpec(
        "Kernel Newbies",
        "rss",
        "https://kernelnewbies.org/recentchanges?action=rss_rc&unique=1&ddiffs=1",
        0.75,
        CredibilityKind.COMMUNITY,
        RssAdapter,
        {
            "name": "Kernel Newbies",
            "url": "https://kernelnewbies.org/recentchanges?action=rss_rc&unique=1&ddiffs=1",
        },
    ),
    SourceSpec(
        "Cloudflare Blog",
        "rss",
        "https://blog.cloudflare.com/rss/",
        0.82,
        CredibilityKind.RESPECTED_PUBLICATION,
        RssAdapter,
        {"name": "Cloudflare Blog", "url": "https://blog.cloudflare.com/rss/"},
    ),
]


def build_adapter(spec: SourceSpec) -> SourceAdapter:
    kwargs = spec.kwargs or {}
    if spec.factory is RssAdapter:
        return RssAdapter(name=spec.name, url=spec.url)
    if spec.factory is None:
        raise ValueError(f"No adapter for {spec.name}")
    return spec.factory(**kwargs) if kwargs else spec.factory()
