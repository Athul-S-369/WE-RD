# Deployment

## Preferred: GitHub Pages publisher

See [github-pages.md](github-pages.md).

Daily Actions write into `data/weird.db` in the repository. Sunday builds a static newspaper and deploys Pages.

## Docker Compose (single host API + web)

```bash
cp .env.example .env
docker compose up --build -d
```

Services: `db` (Postgres + pgvector image), `api` (FastAPI), `web` (Next.js). Optional for local desk; not required for Pages.

## Schema

SQLAlchemy `init_db()` / `weird-migrate` creates tables.  
`database/migrations/001_init.sql` documents the Postgres layout for operators who self-host.

## Production checklist (Pages)

1. Enable Pages → GitHub Actions
2. Set `WEIRD_BASE_PATH` if using a project site
3. Run **Bootstrap Pages** once
4. Optional LLM / YouTube / GitHub secrets for richer discovery
5. Confirm daily + Sunday workflows are enabled

## Health

- Local API: `GET /health`
- Pages: open the published URL after Sunday/bootstrap
