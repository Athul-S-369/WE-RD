# Source exploration

Bounded primary-source fetches during analysis — not a crawler.

## Behavior

When `WEIRD_EXPLORE_SOURCES=true` (default), `analyze_top_stories` fetches up to `WEIRD_EXPLORE_MAX_PER_STORY` source URLs per story:

- http(s) only (`is_safe_http_url`)
- response body capped (~250KB)
- excerpt capped (~12k chars)
- HTML sanitized
- scripts/styles stripped

GitHub / arXiv / generic HTML/text get light kind labels (`readme`, `paper`, `article`, …).

Failures are isolated; exploration never blocks the rest of the pipeline.

## Implementation

`weird.explore.explore_primary_url` / `explore_story_sources`

Excerpts are folded into the analysis prompt as `PRIMARY EXCERPTS` and summarized in `analysis.explorations` (url/ok/kind/title only).

## Disable for offline tests

```bash
WEIRD_EXPLORE_SOURCES=false
```
