# Architecture

```
THE INTERNET
     ↓
DISCOVERY (RSS, HN, Lobsters, GitHub API, arXiv, NVD)
     ↓
SOURCE COLLECTION → NORMALIZATION → DEDUPLICATION
     ↓
STORY CLUSTERING (URL + title + embeddings + entities)
     ↓
TECHNICAL ANALYSIS (LLM, only top candidates)
     ↓
WE-RD / CRACKED / RABBIT-HOLE SCORES
     ↓
SOURCE / CREDIBILITY + enrichment (GitHub, YouTube)
     ↓
DAILY CANDIDATE POOL (not published)
     ↓
SUNDAY EDITORIAL SELECTION → EDITION → PUBLISH (idempotent)
```

## Processes

- `python -m weird.pipeline.daily` — fetch, cluster, score, analyze, enrich
- `python -m weird.pipeline.sunday` — select, generate/validate via LLM, publish issue
- FastAPI (`weird.api:app`) — reader + admin
- Next.js — newspaper

## Cost control

Raw items never all go to an expensive model. Filtering: ingest → dedup → cluster → metadata scores → top N (`WEIRD_MAX_LLM_CANDIDATES`) → LLM. Completions are cached in `llm_cache`.

## LLM providers

`WEIRD_LLM_PROVIDER=mock|openai|anthropic|gemini|local`

Missing cloud/local keys fall back to deterministic mock analysis with an honest `generation_mode` / `mode_label`. See [provider-architecture.md](provider-architecture.md).

Prompt templates live in `packages/core/weird/prompts/` (also mirrored under `packages/prompts/` for editorial editing). Override with `WEIRD_PROMPTS_DIR` if needed.

## Search & graphs

- Hybrid search: [semantic-search.md](semantic-search.md)
- Bounded primary-source fetches: [source-exploration.md](source-exploration.md)
- Related stories / source graph: `weird.graph` exposed on story detail + `/stories/{slug}/graph`
