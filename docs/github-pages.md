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

## Enable once (required)

`actions/configure-pages` **cannot** create a Pages site with the default `GITHUB_TOKEN`. Do this once in the GitHub UI:

1. Open **[Settings → Pages](https://github.com/Athul-S-369/WE-RD/settings/pages)**
2. Under **Build and deployment → Source**, choose **GitHub Actions**
3. Optional repository variable: `WEIRD_BASE_PATH` = `/WE-RD`  
   → paper at `https://athul-s-369.github.io/WE-RD/`
4. Optional secrets (LLM quality only): `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` / `YOUTUBE_API_KEY`
5. Optional auto-enable secret: `WEIRD_PAGES_TOKEN` — classic PAT with **`repo`** scope (only if you refuse the UI step)
6. Actions → **Bootstrap Pages (first deploy)** → Run workflow on **`main`** (latest commit)

If you see `Get Pages site failed` / `Not Found`, step 2 was skipped — enable Pages, then re-run. Do not re-run an old failed job from before Pages was enabled; start a **new** workflow run.

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
