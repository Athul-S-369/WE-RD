# WE-RD

### Things worth falling down a rabbit hole for.

WE-RD is an automated technical-curiosity newspaper that discovers the strangest, most fascinating and technically impressive things happening across the internet and turns them into a weekly publication.

It is pronounced **"weird."** The hyphen is intentional.

> Optimize for fascination — not article volume.

WE-RD is **not** a generic tech-news site, RSS reader, or AI clickbait factory. Every major story answers:

1. *I didn't know this existed.*
2. *How did they actually build that?*
3. *Where is the source code?*

---

## Live demo / GitHub Pages publisher

WE-RD is built to publish **from GitHub, on GitHub**:

```
Daily Actions  →  commit discoveries into data/weird.db
Sunday Actions →  generate edition + deploy static site to GitHub Pages
```

See **[docs/github-pages.md](docs/github-pages.md)** for setup.

Quick enable:

1. Settings → Pages → Source: **GitHub Actions**
2. Set variable `WEIRD_BASE_PATH=/your-repo-name` if using a project site
3. Run workflow **Bootstrap Pages (first deploy)**

### Local stack (optional)

```bash
docker compose up --build
```

Then open:

- Newspaper: [http://localhost:3000](http://localhost:3000)
- API: [http://localhost:8000/docs](http://localhost:8000/docs)
- Desk (admin): [http://localhost:3000/admin](http://localhost:3000/admin) — token from `WEIRD_ADMIN_TOKEN`

Demo mode ships a labeled **ISSUE** with representative stories. Demo content is explicitly marked and is **not** current news.

---

## Why it exists

Technically curious people deserve a weekly machine that finds obscure, clever, unnecessary, and deeply engineered work — then explains **how it works** and opens a path into the source graph.

## What makes it different

| Typical aggregator | WE-RD |
| --- | --- |
| Popularity first | Fascination first (popularity is a weak weight) |
| Headline summaries | How-it-works + under-the-hood layers |
| One article = one story | Clustering + timelines across sources |
| Publish everything | Editorial diversity + quality floors |
| Opaque AI paste | Evidence extraction → claim validation |

---

## Architecture

```
THE INTERNET
     ↓
DISCOVERY (RSS · HN · Lobsters · GitHub · arXiv · NVD …)
     ↓
NORMALIZE → DEDUPE → CLUSTER → SCORE
     ↓
TOP CANDIDATES ONLY → LLM ANALYSIS → VALIDATE
     ↓
GITHUB + YOUTUBE ENRICHMENT
     ↓
DAILY CANDIDATE POOL
     ↓
SUNDAY EDITORIAL SELECTION → EDITION (idempotent)
```

See [docs/architecture.md](docs/architecture.md).

### Stack

- **Frontend:** Next.js, React, TypeScript, Tailwind (static export for GitHub Pages)
- **API:** FastAPI, SQLAlchemy, Pydantic (optional for local desk)
- **Corpus:** SQLite in `data/weird.db` committed by Actions (Postgres still supported for self-host)
- **Publisher:** Daily + Sunday GitHub Actions → GitHub Pages
- **LLM:** pluggable `mock | openai | anthropic | gemini | local` with honest mode labels

---

## Scores

- **WE-RD score** — serious multi-factor interestingness (configurable weights; popularity is not dominant)
- **CRACKED score** — personality meter for technical extremity / absurd ambition
- **Rabbit-hole score** — how many technical paths a story opens

Details: [docs/scoring.md](docs/scoring.md).

---

## Daily & Sunday automation

| Schedule | Job |
| --- | --- |
| Daily | Fetch → dedupe → cluster → score → analyze top N → enrich |
| Sunday | Select → validate → publish issue (idempotent by `week_start`) |

Workflows live in `.github/workflows/`. For production, point `DATABASE_URL` at a durable Postgres (Actions' service containers are ephemeral by default).

---

## Local development

### Docker (recommended)

```bash
cp .env.example .env
docker compose up --build
```

### Zero-key SQLite demo

```bash
# .env
DATABASE_URL=sqlite:///./weird-local.db
WEIRD_LLM_PROVIDER=mock
WEIRD_DEMO_MODE=true
WEIRD_EMBEDDING_BACKEND=hashed

pip install -e ".[dev]"
weird-migrate
weird-seed
uvicorn weird.api:app --reload --port 8000
```

### Without Docker (Postgres)

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e ".[dev]"
weird-migrate
weird-seed
uvicorn weird.api:app --reload --port 8000

cd apps/web && npm install && npm run dev
```

### Pipeline CLIs

```bash
weird-daily
weird-sunday
```

### Tests

```bash
pip install -e ".[dev]"
pytest -q
```

---

## Environment variables

See [`.env.example`](.env.example). Important knobs:

| Variable | Purpose |
| --- | --- |
| `WEIRD_DEMO_MODE` | Seed labeled demo edition on API start |
| `WEIRD_LLM_PROVIDER` | `mock` (default) / `openai` / `anthropic` / `gemini` / `local` |
| `WEIRD_ADMIN_TOKEN` | Protects `/admin/*` and the desk UI |
| `WEIRD_EMBEDDING_BACKEND` | `auto` / `hashed` / `sentence-transformers` |
| `WEIRD_USE_PGVECTOR` | Dual-write embeddings to pgvector (Postgres only) |
| `GITHUB_TOKEN` | Optional GitHub trending / richer enrichment |
| `YOUTUBE_API_KEY` | Optional video discovery (else `NO VIDEO FOUND`) |
| `WEIRD_WEIGHT_*` | Interestingness weights |

Without API keys the mock LLM and demo seed keep the product fully runnable.

---

## Adding a source

1. Add a spec in `packages/core/weird/ingestion/catalog.py`
2. Implement an adapter returning `NormalizedItem` (see `ingestion/base.py`)
3. Prefer official APIs / RSS; respect robots and ToS
4. Document credibility kind + score

More: [docs/ingestion.md](docs/ingestion.md).

---

## Example story shape

**WE-RD / BUILD — The C library that got rebuilt in Rust**

Not: “Someone rewrote a C library in Rust.”

Instead: ABI compatibility → FFI → ownership → POSIX shims → tests → author-reported benchmarks only → **GO TECHNICAL** → repository / notes / talks.

---

## Documentation

- [Architecture](docs/architecture.md)
- [Ingestion](docs/ingestion.md)
- [Editorial system](docs/editorial-system.md)
- [Scoring](docs/scoring.md)
- [Semantic search](docs/semantic-search.md)
- [Source exploration](docs/source-exploration.md)
- [Provider architecture](docs/provider-architecture.md)
- [Deployment](docs/deployment.md)
- [Operations](docs/operations.md)

## License

MIT — see [LICENSE](LICENSE).

## Contributing

PRs that improve discovery quality, factuality, or rabbit-hole paths are preferred over UI chrome. Keep secrets out of the repo. Label demo content clearly. Do not sensationalize security or leaks.
