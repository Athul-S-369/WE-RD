# Editorial system

## Daily = candidates, Sunday = newspaper

Daily runs build the week's pool. Nothing is published until Sunday selection.

## Selection principles

`weird.pipeline.editorial.select_edition_stories`:

- Prefer **WE-RD score**, **CRACKED**, **rabbit-hole**, credibility
- Honor structured **editorial evaluator** JSON on `story.extra.editorial` (`keep` / `publish_ready`)
- Enforce **category diversity** — avoid five near-identical Rust rewrites
- **Quality over fill** — empty sections beat weak filler
- Featured story = highest combined fascination signal for **THE BIG WE-RD**

The evaluator runs during analyze (`prompts/editorial.txt`) via the active LLM provider, with a deterministic heuristic fallback (`weird.analysis_fallback.editorial_heuristic`).

## Edition sections

Typical Sunday layout:

- THE BIG WE-RD
- HOW THE HELL DID THEY BUILD THIS?
- WHY DOES THIS EXIST?
- DEEP END / BREAK / LANG / MACHINE / AI / LAB / SOURCE / WATCH / RABBIT HOLE

## Writing rules

- How it works > what happened
- Never invent benchmarks or CVE details
- If evidence is thin: *“The available sources do not establish this.”*
- Security: status labels (`DISCLOSED`, `CONFIRMED`, `THEORETICAL`, …) — no exploitation recipes
- Leaks: `UNVERIFIED` / `CORROBORATED` / `CONFIRMED` — never promote rumor to fact

## Idempotent publish

`publish_sunday` keys editions on `week_start`. A second Sunday run returns the existing published issue instead of duplicating.

## GO TECHNICAL

Every major story exposes layers:

1. Quick read (30–60s)
2. Technical read
3. Source dive (GitHub, papers, docs, talks)
