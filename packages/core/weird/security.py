from __future__ import annotations

import bleach

ALLOWED_TAGS = ["p", "br", "em", "strong", "code", "pre", "a", "ul", "ol", "li", "blockquote"]
ALLOWED_ATTRS = {"a": ["href", "title", "rel"]}


def sanitize_html(value: str | None) -> str:
    if not value:
        return ""
    return bleach.clean(value, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)


def is_safe_http_url(url: str) -> bool:
    return url.startswith("https://") or url.startswith("http://")
