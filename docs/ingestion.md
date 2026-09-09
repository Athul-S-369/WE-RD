# Ingestion

## Goal

Discover high-signal technical curiosities from public, preferably API/RSS sources. One broken source must never stop the rest of the pipeline.

## Adapters

All adapters implement the same contract (`NormalizedItem`):

- `title`, `url`, `author`, `published_at`
- `content` / `summary`
- `extra` (stars, score, tags, …)

Registered in `packages/core/weird/ingestion/catalog.py`:

| Adapter | Notes |
| --- | --- |
| RSS | LWN, Phoronix, USENIX, Cloudflare Blog, Kernel Newbies, … |
| Hacker News | Official Firebase API |
| Lobsters | JSON / RSS |
| GitHub | Search when `GITHUB_TOKEN` is set; empty otherwise (no brittle HTML scrape) |
| arXiv | Atom API |
| CVE / NVD | Public CVE feeds |

Dedup: canonical URL + content hash + title similarity; optional semantic near-dup when embeddings are supplied.

## Pipeline step

`weird.pipeline.ingest.ingest_all`:

1. Ensure source rows exist
2. Fetch per adapter (isolated try/except)
3. Reject non-http(s) URLs
4. Canonical URL + title/content-hash dedupe
5. Sanitize HTML before store
6. Record `last_fetched_at` / `last_error`

## Cost control

Raw items are **not** sent to an LLM. Downstream stages filter → cluster → score → top N (`WEIRD_MAX_LLM_CANDIDATES`).

## Adding a source

1. Prefer official APIs or RSS over scraping.
2. Do not automate sites that prohibit it.
3. Assign `credibility_kind` and `credibility_score` honestly (anonymous posts stay unverified).
4. Cover failure modes (timeouts, malformed feeds) — the adapter should raise; ingest will log and continue.
