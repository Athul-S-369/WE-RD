# Scoring

Three scores, three jobs.

## WE-RD score (signal)

Configurable weighted blend (`WEIRD_WEIGHT_*` in `.env`):

| Factor | Intent |
| --- | --- |
| Novelty / originality / unexpectedness | “I didn't know this existed” |
| Difficulty / depth | Engineering seriousness |
| Educational / rabbit-hole | Learning paths |
| Credibility | Primary sources beat anonymous posts |
| Impact | Present but moderated |
| Community | **Weak** — stars/upvotes must not dominate |

Popularity is intentionally underweighted so a 70-star repo can beat a viral recap.

## CRACKED score

Editorial personality meter (0–100) for technical extremity / absurd ambition.

Example blurb: *“Someone absolutely did not need to build this.”*

Fun in the UI. Not a substitute for factual ranking.

## Rabbit-hole score

Estimates how many distinct technical paths a story opens (languages, ABIs, kernels, papers, …). High when a reader can lose half an hour following links.

## Implementation

`packages/core/weird/scoring.py` — heuristic + keyword/entity signals today; LLM classification can refine category tags for top candidates without replacing the deterministic score base.

Each `ScoreBreakdown` stores:

- `dimensions` — raw 0–100 component scores
- `weights` — normalized env weights
- `contributions` — dimension × weight (sums to signal)
- `explanations` — short human-readable component intents

Stored on `story.extra` and exposed via story detail `score_breakdown` and card `score_dimensions`.
