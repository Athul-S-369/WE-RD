# GitHub Pages publisher

WE-RD is designed to run as a **GitHub-native automated newspaper**:

```
Mon–Sat (Actions)
  fetch → cluster → score → enrich
  commit into data/weird.db   ← the repo is the notebook

Sunday (Actions)
  editorial select → export JSON → static Next build
  deploy to GitHub Pages
```

No always-on Postgres is required for the default publisher path.

## Enable once (required for a public URL)

`GITHUB_TOKEN` can **deploy** files but usually **cannot create** a Pages site. Prefer Path A:

### Path A — Branch deploy (simplest)

Bootstrap pushes the static site to the **`gh-pages`** branch when Actions Pages is not configured.

1. Run **Bootstrap Pages (first deploy)**
2. Open **[Settings → Pages](https://github.com/Athul-S-369/WE-RD/settings/pages)**
3. Source: **Deploy from a branch**
4. Branch: **gh-pages** / **/(root)** → Save
5. Paper: `https://athul-s-369.github.io/WE-RD/`

### Path B — GitHub Actions deploy

1. Settings → Pages → Source: **GitHub Actions**
2. Variable `WEIRD_BASE_PATH` = `/WE-RD`
3. Run bootstrap (uses `deploy-pages`)

### Optional

- LLM secrets: `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` / `YOUTUBE_API_KEY`
- `WEIRD_PAGES_TOKEN` (classic PAT, **repo** scope) — create/update Pages via API
- Variable `WEIRD_BASE_PATH=/WE-RD` so asset paths work on the project site

## Weekly automation

| Workflow | When | What |
| --- | --- | --- |
| `daily.yml` | Every day 06:00 UTC | Discovery into `data/weird.db`, commit |
| `sunday.yml` | Sunday 08:00 UTC | Publish issue, export `apps/web/public/content/`, deploy Pages |
| `pages-bootstrap.yml` | Manual | Seed demo + first Pages deploy |

Pipeline commits are authored as **Athul S** (`176425883+Athul-S-369@users.noreply.github.com`) so they count on the [contribution graph](https://github.com/Athul-S-369) when they land on `main` or `gh-pages`.

## Corpus layout

```
data/
  weird.db                 # durable SQLite corpus (committed)
  pipeline/daily-YYYYMMDD.json
  last-export.json
apps/web/public/content/
  current.json
  editions.json
  editions/{n}.json
  stories/{slug}.json
  stories-index.json
  meta.json
```

## Local publisher dry-run

```bash
export DATABASE_URL=sqlite:///./data/weird.db
export WEIRD_DEMO_MODE=true
pip install -e .
python -m weird.db
python -m weird.seed
python -m weird.pipeline.export_site

cd apps/web
WEIRD_STATIC_EXPORT=1 NEXT_PUBLIC_STATIC=1 npm run build
# open apps/web/out/index.html via any static server
```

## Notes

- Publishing is **idempotent** per ISO week (`week_start` unique).
- Demo stories stay labeled; bootstrap uses them when the corpus is empty.
- The admin desk still needs a live API (local/docker); Pages serves the reader newspaper only.
