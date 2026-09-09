"""Evidence-first deterministic analysis used when LLM is mock/unavailable."""

from __future__ import annotations

import re
from typing import Any

from weird.scoring import extract_tags


def evidence_first_analysis(*, title: str, text: str, category: str, sources: str = "") -> dict[str, Any]:
    excerpt = _first_sentences(text, 2) or f"Sources describe {title}."
    tags = extract_tags(f"{title}\n{text}")
    repo_mentions = re.findall(r"https?://github\.com/[\w.-]+/[\w.-]+", text + "\n" + sources)
    paper_mentions = re.findall(r"https?://arxiv\.org/\S+", text + "\n" + sources)
    has_primary = bool(repo_mentions or paper_mentions or "github.com" in (sources + text).lower())

    how = (
        "From the available material, the work proceeds as a layered implementation: "
        "interface boundaries, internals, tests, then compatibility with the surrounding ecosystem."
    )
    if "rewrite" in text.lower() or "rewrote" in text.lower():
        how = (
            "The sources describe a rewrite path: preserve observable behavior, replace internals, "
            "and validate with compatibility tests before claiming parity."
        )
    if "compiler" in text.lower() or "llvm" in text.lower():
        how = (
            "Available sources point at a compiler/toolchain shaped pipeline — front-end, IR or "
            "intermediate representation, and backend concerns — without inventing unstated passes."
        )

    under = (
        "Inspect the primary repository and any linked papers before treating details as settled. "
        "This fallback analyzer will not invent architecture the sources do not describe."
    )
    if repo_mentions:
        under = (
            f"Primary code appears linked ({repo_mentions[0]}). Prefer the repository README, "
            "issues, and tests over secondary recaps."
        )

    return {
        "why_you_should_care": (
            "The interesting part is not the headline. It is the implementation: "
            "constraints, trade-offs, and the path from idea to working system."
        ),
        "what_happened": excerpt,
        "how_it_works": how,
        "under_the_hood": under,
        "why_they_built_it": _why(text),
        "what_was_difficult": (
            "Compatibility, correctness, and the unglamorous work of matching existing behavior "
            "are the recurring hard parts in the source material."
        ),
        "performance": "The available sources do not establish independent benchmark numbers.",
        "trade_offs": "Gains in one dimension (safety, control, size, or weirdness) are paid for in another.",
        "what_is_surprising": "Someone chose the harder path and then documented enough of it to follow.",
        "quick_read": excerpt[:280] or title,
        "rabbit_holes": tags[:6] or ["implementation", "testing", "compatibility"],
        "further_reading_notes": "Prefer the original repository, papers, and talks over secondary recaps.",
        "category": category,
        "evidence": {
            "has_primary_source": has_primary,
            "repos": repo_mentions[:5],
            "papers": paper_mentions[:5],
            "tags": tags,
        },
        "generation_mode": "deterministic_fallback",
    }


def editorial_heuristic(story_payload: dict[str, Any]) -> dict[str, Any]:
    """Structured editorial evaluator that works with zero API keys."""
    signal = float(story_payload.get("signal_score") or 0)
    cracked = int(story_payload.get("cracked_score") or 0)
    rabbit = float(story_payload.get("rabbit_hole_score") or 0)
    confidence = str(story_payload.get("confidence") or "unverified")
    has_primary = bool((story_payload.get("evidence") or {}).get("has_primary_source"))
    keep = signal >= 48 or cracked >= 70
    diversity_risk = "low"
    if story_payload.get("category") in {"AI"} and signal < 65:
        diversity_risk = "medium"
    return {
        "keep": keep,
        "publish_ready": keep and confidence != "rumor",
        "quality_floor_met": keep,
        "primary_source_present": has_primary,
        "scores": {
            "editorial": round(signal * 0.55 + cracked * 0.2 + rabbit * 0.25, 2),
            "signal": signal,
            "cracked": cracked,
            "rabbit_hole": rabbit,
        },
        "risks": []
        if has_primary
        else ["No clear primary repository/paper detected — prefer linking one before publish."],
        "diversity_risk": diversity_risk,
        "notes": "Heuristic editorial evaluator (no cloud LLM).",
        "generation_mode": "deterministic_fallback",
    }


def _why(text: str) -> str:
    lower = text.lower()
    if "for fun" in lower or "just because" in lower or "unnecessary" in lower:
        return "The sources frame this as curiosity-driven or deliberately unnecessary engineering."
    if "security" in lower or "cve" in lower:
        return "The sources point at a security or correctness pressure that forced a deeper look."
    return "The sources point to curiosity, necessity, or a bet that the existing stack was the wrong shape."


def _first_sentences(text: str, n: int = 2) -> str:
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    if not cleaned:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    return " ".join(parts[:n])[:500]
