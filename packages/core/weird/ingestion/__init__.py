from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class NormalizedItem:
    source_name: str
    source_type: str
    title: str
    url: str
    author: str | None = None
    published_at: datetime | None = None
    content: str = ""
    summary: str = ""
    extra: dict[str, Any] = field(default_factory=dict)
