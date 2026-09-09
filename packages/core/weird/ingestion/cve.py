from __future__ import annotations

from datetime import datetime, timezone

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from weird.config import get_settings
from weird.ingestion import NormalizedItem
from weird.ingestion.base import SourceAdapter

NVD = "https://services.nvd.nist.gov/rest/json/cves/2.0"


class CveAdapter(SourceAdapter):
    name = "NVD CVE"
    source_type = "cve"

    def __init__(self, results: int = 30):
        self.results = results

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3), reraise=True)
    def fetch(self) -> list[NormalizedItem]:
        timeout = get_settings().weird_http_timeout
        with httpx.Client(timeout=timeout) as client:
            data = client.get(NVD, params={"resultsPerPage": self.results}).json()
        items: list[NormalizedItem] = []
        for vuln in data.get("vulnerabilities", []):
            cve = vuln.get("cve", {})
            cve_id = cve.get("id") or ""
            descs = cve.get("descriptions") or []
            english = next((d.get("value") for d in descs if d.get("lang") == "en"), "")
            published = None
            if cve.get("published"):
                published = datetime.fromisoformat(cve["published"].replace("Z", "+00:00"))
                if published.tzinfo is None:
                    published = published.replace(tzinfo=timezone.utc)
            items.append(
                NormalizedItem(
                    source_name=self.name,
                    source_type="cve",
                    title=cve_id,
                    url=f"https://nvd.nist.gov/vuln/detail/{cve_id}",
                    published_at=published,
                    content=english,
                    extra={"cve": cve_id},
                )
            )
        return items
