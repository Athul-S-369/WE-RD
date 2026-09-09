# Provider architecture

## Principle

Optional providers only. Core must run with **zero** OpenAI / Anthropic / Gemini / YouTube / GitHub keys.

## LLM

`WEIRD_LLM_PROVIDER=mock|openai|anthropic|gemini|local`

| Provider | When | Label |
| --- | --- | --- |
| `mock` | Default / demo | `deterministic_fallback` |
| `openai` / `anthropic` / `gemini` | Cloud keys present | `cloud_*` |
| `local` | `WEIRD_LOCAL_LLM_URL` set | `local_llm` |

Missing keys **fall back to mock** with an honest `mode_label` such as `deterministic_fallback (openai key missing)`.

Analysis JSON always carries `generation_mode`. The UI surfaces processing mode on story pages and `/capabilities`.

Prompts live in `packages/core/weird/prompts/` (`facts`, `analyze`, `validate`, `classify`, `editorial`).

## Embeddings

`WEIRD_EMBEDDING_BACKEND=auto|hashed|sentence-transformers`

Auto tries local sentence-transformers, else hashed BoW. Never pretends a neural model ran if it did not.

## YouTube

Provider abstraction in `weird.enrichment.youtube`:

- API key → YouTube Data API
- No key → empty results with status **`NO VIDEO FOUND`**
- Never fabricate video IDs

## GitHub

Public API works without a token (rate-limited). With `GITHUB_TOKEN`, enrichment adds languages, README excerpt, license, topics more reliably.

## Honesty endpoint

`GET /capabilities` and admin health `processing_mode` advertise what is actually active.
