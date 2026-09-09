# Operations

## Daily

```bash
weird-daily
# or
python -m weird.pipeline.daily
```

Fetch → dedupe → cluster → score → analyze top N → enrich (GitHub / YouTube).

## Sunday

```bash
weird-sunday
# or
python -m weird.pipeline.sunday
```

Re-analyze/enrich if needed → editorial selection (quality floor + diversity + evaluator) → idempotent publish by `week_start`.

## Admin desk

- UI: `/admin` with `WEIRD_ADMIN_TOKEN`
- `POST /admin/pipeline/daily|sunday`
- Health includes source errors, run metrics, and **processing mode**

## Zero-key local path

```bash
cp .env.example .env
# DATABASE_URL=sqlite:///./weird-local.db
# WEIRD_LLM_PROVIDER=mock
# WEIRD_DEMO_MODE=true
pip install -e ".[dev]"
weird-migrate
weird-seed
uvicorn weird.api:app --reload --port 8000
```

Frontend: `cd apps/web && npm install && npm run dev`

## Postgres + pgvector

```bash
docker compose up --build
# optional: WEIRD_USE_PGVECTOR=true
```

## GitHub Actions

Workflows under `.github/workflows/`. Point `DATABASE_URL` at durable Postgres for production — Actions service containers are ephemeral by default.

## Honesty checklist

- No fabricated week-in-numbers (DB metrics only)
- No fake YouTube IDs
- Analysis `generation_mode` reflects mock vs cloud vs local
- Search `/capabilities` reports embedding backend actually used
