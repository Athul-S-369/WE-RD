from __future__ import annotations

import hashlib
import re
from typing import Any

from weird.analysis_fallback import editorial_heuristic, evidence_first_analysis
from weird.config import Settings
from weird.llm import LLMProvider


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:80]


class MockProvider(LLMProvider):
    name = "mock"
    mode_label = "deterministic_fallback"

    def __init__(self, settings: Settings):
        self.settings = settings

    def complete_json(self, prompt_name: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
        title = kwargs.get("title") or _extract(prompt, "Title:") or "Untitled discovery"
        body = kwargs.get("text") or prompt
        category = kwargs.get("category") or "BUILD"
        if prompt_name == "classify":
            return {
                "category": category,
                "tags": kwargs.get("tags") or ["Engineering"],
                "keep": True,
                "reason": "Heuristic classification in mock mode.",
                "generation_mode": self.mode_label,
            }
        if prompt_name == "facts":
            return {
                "facts": [
                    {
                        "claim": f"{title} is described by the collected sources.",
                        "supported": True,
                        "source_hint": "primary",
                    }
                ],
                "unsupported": [],
                "generation_mode": self.mode_label,
            }
        if prompt_name == "analyze":
            analysis = evidence_first_analysis(
                title=title, text=body, category=category, sources=kwargs.get("sources") or ""
            )
            analysis["generation_mode"] = self.mode_label
            return analysis
        if prompt_name == "validate":
            return {"ok": True, "issues": [], "rewrites": {}, "generation_mode": self.mode_label}
        if prompt_name == "editorial":
            payload = {
                "signal_score": kwargs.get("signal_score", 0),
                "cracked_score": kwargs.get("cracked_score", 0),
                "rabbit_hole_score": kwargs.get("rabbit_hole_score", 0),
                "confidence": kwargs.get("confidence", "unverified"),
                "category": category,
                "evidence": kwargs.get("evidence") or {},
            }
            result = editorial_heuristic(payload)
            result["generation_mode"] = self.mode_label
            return result
        digest = hashlib.sha256(prompt.encode()).hexdigest()[:12]
        return {"mock": True, "prompt_name": prompt_name, "digest": digest, "generation_mode": self.mode_label}


def _extract(prompt: str, marker: str) -> str | None:
    if marker not in prompt:
        return None
    return prompt.split(marker, 1)[1].splitlines()[0].strip()
