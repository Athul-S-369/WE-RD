# WE-RD

### Things worth falling down a rabbit hole for.

**WE-RD** (pronounced *weird*) is an automated technical-curiosity newspaper. It discovers obscure, clever, and deeply engineered work across the internet, scores it for fascination — not popularity — and publishes a weekly broadsheet that answers three questions for every story:

1. *I didn't know this existed.*
2. *How did they actually build that?*
3. *Where is the source code?*

> Optimize for fascination — not article volume.

---

## What it is

| Not this | This |
| --- | --- |
| Generic tech aggregator | Fascination-first editorial machine |
| Headline summarizer | How-it-works + under-the-hood layers |
| One URL = one story | Multi-source clusters + timelines |
| Publish everything | Quality floors + category diversity |
| Opaque AI paste | Evidence extraction → claim validation |

Live paper (GitHub Pages): after Actions publish → `https://athul-s-369.github.io/WE-RD/`

---

## System overview

```mermaid
flowchart TB
  subgraph sources [Discovery surface]
    HN[Hacker News]
    LB[Lobsters]
    GH[GitHub]
    AX[arXiv]
    RSS[RSS / CVE / more]
  end

  subgraph daily [Daily pipeline]
    IN[Ingest · normalize]
    DD[Dedupe · embed · cluster]
    SC[Multi-factor scoring]
    LLM[Top-N LLM analyze + validate]
    EN[GitHub · YouTube enrich]
    POOL[(Candidate pool<br/>data/weird.db)]
  end

  subgraph sunday [Sunday publish]
    ED[Editorial select]
    PUB[Idempotent edition]
    EXP[JSON export]
    WEB[Next.js static build]
    PAGES[GitHub Pages]
  end

  sources --> IN --> DD --> SC --> LLM --> EN --> POOL
  POOL --> ED --> PUB --> EXP --> WEB --> PAGES
```

The repository itself is the durable notebook: daily Actions commit discoveries into `data/weird.db`; Sunday Actions cut an issue and deploy a static newspaper.

---

## Monorepo map

```text
WE-RD/
├── packages/core/weird/     # FastAPI · pipeline · scoring · LLM · DB
├── packages/prompts/        # Editable editorial prompts
├── apps/web/                # Next.js 15 newspaper (paper + static export)
├── data/weird.db            # GitHub-native SQLite corpus
├── database/migrations/     # Schema
├── .github/workflows/       # daily · sunday · pages-bootstrap · test
└── docs/                    # Deep dives (architecture, scoring, search…)
```

| Layer | Tech |
| --- | --- |
| Reader UI | Next.js 15, React, TypeScript, Tailwind — broadsheet + bento layout |
| Core | Python, FastAPI, SQLAlchemy, Pydantic |
| Corpus | SQLite (`data/weird.db`) committed by Actions; Postgres/pgvector optional |
| Intelligence | Pluggable LLM (`mock` · OpenAI · Anthropic · Gemini · local) |
| Publish | Static JSON under `apps/web/public/content/` → `out/` → Pages |

---

## Pipeline architecture

```mermaid
sequenceDiagram
  participant Net as The internet
  participant Daily as weird.pipeline.daily
  participant DB as data/weird.db
  participant Sun as weird.pipeline.sunday
  participant Web as apps/web
  participant Pages as GitHub Pages

  Net->>Daily: RSS · HN · Lobsters · GitHub · arXiv · NVD
  Daily->>Daily: normalize → cluster → score
  Daily->>Daily: LLM top-N only (cost gate)
  Daily->>DB: upsert stories · enrichment · run log
  Note over DB: Mon–Sat commits

  Sun->>DB: re-score · editorial select
  Sun->>DB: Edition(week_start) idempotent
  Sun->>Web: export_site → public/content/*.json
  Web->>Pages: WEIRD_STATIC_EXPORT=1 → out/
```

| Stage | Module | Role |
| --- | --- | --- |
| Ingest | `ingestion/*`, `catalog.py` | Source adapters → `NormalizedItem` |
| Process | `pipeline/process.py`, `clustering.py` | Embed, cluster, upsert `Story` |
| Score | `scoring.py` | WE-RD · CRACKED · rabbit-hole |
| Analyze | `pipeline/analyze.py`, `explore.py` | Bounded source dive + LLM facts/validate |
| Enrich | `enrichment/github.py`, `youtube.py` | Repos, stars, talks — never invent |
| Editorial | `pipeline/editorial.py` | Floors, diversity, featured pick |
| Publish | `pipeline/publish.py` | One edition per ISO `week_start` |
| Export | `pipeline/export_site.py` | Static content graph for Pages |

---

## Scoring model

Popularity is a **weak** signal. Interestingness is a weighted blend of technical dimensions:

```mermaid
flowchart LR
  subgraph dimensions [Signal dimensions]
    N[novelty]
    D[difficulty]
    O[originality]
    DP[depth]
    I[impact]
    E[educational]
    C[credibility]
    R[rarity]
    U[unexpectedness]
    CM[community · weak]
    RH[rabbit_hole]
  end

  dimensions --> W[Configurable WEIRD_WEIGHT_*]
  W --> S[WE-RD signal_score]
  U & D & N & RH --> K[CRACKED personality blend]
  K --> CS[cracked_score 0–100]
  RH --> RP[rabbit_hole_score + paths]
```

| Meter | Meaning |
| --- | --- |
| **WE-RD score** | Serious multi-factor interestingness (`ScoreBreakdown` is explainable) |
| **CRACKED score** | Technical extremity / absurd ambition (UI meter + blurb) |
| **Rabbit-hole** | How many technical paths the story opens into source / concepts |

Security and leak status are labeled responsibly — status and context, not exploit recipes.

---

## Intelligence stack

```mermaid
flowchart TB
  subgraph gate [Cost & honesty]
    TOP[Top WEIRD_MAX_LLM_CANDIDATES only]
    CACHE[(LlmCache)]
    MODE[processing_mode labels]
  end

  subgraph providers [Provider bus]
    M[mock · deterministic fallback]
    O[openai]
    A[anthropic]
    G[gemini]
    L[local OpenAI-compatible]
  end

  TOP --> providers
  providers --> CACHE
  providers --> MODE
  MODE --> UI[Newspaper · capabilities API]
```

- Missing API keys fall back to **mock** with an honest mode label — never fake “GPT said.”
- Prompts live as editable text: facts → analyze → validate → classify → editorial.
- Heuristic `analysis_fallback.py` keeps the paper usable with zero keys.
- Hybrid search: BM25-lite + hashed embeddings (always-on) or optional sentence-transformers / pgvector.
- Source graphs (`graph.py`) and bounded HTTP exploration (`explore.py`) deepen rabbit holes without becoming a crawler.

---

## Data model (core)

```mermaid
erDiagram
  Source ||--o{ Article : publishes
  Article }o--o{ Story : clustered_into
  Story ||--o{ StorySource : cites
  Story ||--o{ StoryTimeline : events
  Story ||--o{ Project : links
  Story ||--o{ Video : optional
  Edition ||--o{ EditionStory : contains
  Story ||--o{ EditionStory : featured_in
  Story ||--o| LlmCache : analyzed_by

  Story {
    string slug
    float signal_score
    int cracked_score
    float rabbit_hole_score
    json analysis
    json score_breakdown
  }
  Edition {
    int issue_number
    date week_start
    json week_in_numbers
    string masthead
  }
```

Week-in-numbers are **pipeline counts only** — never fabricated for drama.

---

## Reader surface

The frontend is a newspaper, not a SaaS dashboard: masthead, front-page lead, section bentos, cracked meters, and story-linked diagrams.

```text
apps/web/app/
  /                     Front page (edition.current)
  /issue/[n]            Archive issue
  /story/[slug]         Narrative + scores + source graph
  /story/[slug]/technical   Deeper how-it-works path
  /category/[slug]      Section rails
  /search               Client hybrid search (static-safe)
```

`lib/api.ts` dual-reads: live FastAPI in desk mode, or `public/content/*.json` when `WEIRD_STATIC_EXPORT=1` for Pages.

---

## Automation

```mermaid
flowchart LR
  CRON1["daily.yml<br/>06:00 UTC"] --> DB[(data/weird.db commit)]
  CRON2["sunday.yml<br/>08:00 UTC Sun"] --> DB
  CRON2 --> JSON[public/content]
  CRON2 --> OUT[apps/web/out]
  OUT --> GP[GitHub Pages]
  BOOT[pages-bootstrap.yml] -.-> OUT
  TEST[test.yml · pytest] --> CI[PR / push]
```

| Workflow | Cadence | Effect |
| --- | --- | --- |
| `daily.yml` | Every day | Discover → score → enrich → commit corpus |
| `sunday.yml` | Sundays | Editorial cut → static build → deploy Pages |
| `pages-bootstrap.yml` | Manual | First seed + first deploy |
| `test.yml` | Push / PR | Pipeline · scoring · API · export suite |

---

## Design constraints (non-negotiable)

- **Fascination > volume** — quality floors beat fill quotas  
- **Evidence before eloquence** — validate claims; label confidence  
- **Rabbit holes over recaps** — source code, talks, related graphs  
- **Honest modes** — mock / fallback never masquerades as a paid model  
- **Repo-as-corpus** — the notebook survives without an always-on database  

---

## Documentation

| Doc | Topic |
| --- | --- |
| [Architecture](docs/architecture.md) | End-to-end system |
| [Ingestion](docs/ingestion.md) | Source adapters |
| [Editorial system](docs/editorial-system.md) | Selection & diversity |
| [Scoring](docs/scoring.md) | Weights & meters |
| [Semantic search](docs/semantic-search.md) | Hybrid retrieval |
| [Source exploration](docs/source-exploration.md) | Bounded fetch |
| [Provider architecture](docs/provider-architecture.md) | LLM bus |
| [GitHub Pages](docs/github-pages.md) | Publisher path |

---

## License

MIT — see [LICENSE](LICENSE).

PRs that improve discovery quality, factuality, or rabbit-hole paths beat UI chrome. Do not sensationalize security or leaks.
