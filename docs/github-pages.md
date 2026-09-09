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

## Enable once

1. Push this repository to GitHub.
2. Prefer **Settings → Pages → Source: GitHub Actions** (or let bootstrap auto-enable via `configure-pages` `enablement: true`).
3. Repository variable (required for project sites):
   - `WEIRD_BASE_PATH` = `/WE-RD` → paper at `https://<user>.github.io/WE-RD/`
4. Optional secrets (quality accelerators, not required):
   - `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY`
   - `YOUTUBE_API_KEY`
   - `GITHUB_TOKEN` is provided automatically; a PAT only helps rate limits
5. Run workflow **Bootstrap Pages (first deploy)** manually.

If bootstrap fails with `Get Pages site failed` / `Not Found`, Pages was never created — set Source to **GitHub Actions** in Settings, then re-run the workflow.

Your newspaper will appear at:

`https://<user>.github.io/<repo>/`  
(or your custom domain)

## Weekly automation

| Workflow | When | What |
| --- | --- | --- |
| `daily.yml` | Every day 06:00 UTC | Discovery into `data/weird.db`, commit |
| `sunday.yml` | Sunday 08:00 UTC | Publish issue, export `apps/web/public/content/`, deploy Pages |
| `pages-bootstrap.yml` | Manual | Seed demo + first Pages deploy |

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
