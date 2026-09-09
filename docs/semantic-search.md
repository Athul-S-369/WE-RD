# Semantic search

WE-RD search is **hybrid**: keyword signals + local embeddings + metadata filters.

## Modes

| Layer | Default | Notes |
| --- | --- | --- |
| Keyword | token overlap + lightweight BM25 | Always on, zero dependencies |
| Semantic | hashed bag-of-words (96-d) | Deterministic; no model download |
| Optional semantic | `sentence-transformers` | If installed and `WEIRD_EMBEDDING_BACKEND=auto` or `sentence-transformers` |
| Metadata | category, tag, min_score, confidence | Applied before / with ranking |
| Vector store | JSON on `articles.embedding` | Optional Postgres `pgvector` side table when `WEIRD_USE_PGVECTOR=true` |

## API

`GET /search?q=&category=&tag=&min_score=&confidence=`

Response includes `mode` describing which backends are active. Never claims cloud embeddings if hashed fallback was used.

`GET /capabilities` exposes search + LLM + embedding honesty labels.

## Implementation

- `weird.embeddings` — tokenize, hashed/TF-IDF helpers, BM25-lite, hybrid rank
- `weird.search` — story corpus hybrid search
- `weird.vectorstore` — optional `CREATE EXTENSION vector` + `article_embeddings`

## Ops notes

- SQLite demos: keep `WEIRD_USE_PGVECTOR=false`
- Postgres: use `pgvector/pgvector:pg16` (compose default) and set `WEIRD_USE_PGVECTOR=true` to dual-write
