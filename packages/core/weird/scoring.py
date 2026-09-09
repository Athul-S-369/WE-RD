from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from weird.config import Settings, get_settings
from weird.constants import cracked_blurb
from weird.textutil import tokenize

TECH_HINTS = {
    "compiler",
    "kernel",
    "abi",
    "ffi",
    "llvm",
    "wasm",
    "gpu",
    "cuda",
    "riscv",
    "filesystem",
    "osdev",
    "emulator",
    "jit",
    "parser",
    "bytecode",
    "hypervisor",
    "firmware",
    "microarchitecture",
    "syscall",
    "linker",
    "allocator",
    "concurrency",
    "distributed",
    "raft",
    "quic",
    "tls",
    "cve",
    "exploit",
    "sandbox",
    "interpreter",
    "type system",
    "proof",
    "formal",
}

WEIRD_HINTS = {
    "from scratch",
    "rewrote",
    "rewrite",
    "in c",
    "in rust",
    "unnecessary",
    "for fun",
    "just because",
    "tiny",
    "500 lines",
    "one file",
    "bootstrapped",
    "self-hosted",
    "no dependencies",
    "bizarre",
    "absurd",
    "over-engineered",
}

RABBIT_CONCEPTS = [
    "rust",
    "c",
    "c++",
    "abi",
    "ffi",
    "memory safety",
    "llvm",
    "compilers",
    "operating systems",
    "kernels",
    "posix",
    "networking",
    "databases",
    "gpus",
    "type systems",
    "security",
    "reverse engineering",
    "hardware",
    "filesystems",
    "browsers",
    "virtual machines",
    "formal methods",
    "performance",
    "concurrency",
]


@dataclass
class ScoreBreakdown:
    dimensions: dict[str, float]
    contributions: dict[str, float]
    weights: dict[str, float]
    signal: float
    cracked: int
    rabbit_hole: float
    rabbit_paths: list[str] = field(default_factory=list)
    cracked_blurb: str = ""
    explanations: dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "dimensions": self.dimensions,
            "contributions": self.contributions,
            "weights": self.weights,
            "signal": self.signal,
            "cracked": self.cracked,
            "rabbit_hole": self.rabbit_hole,
            "rabbit_paths": self.rabbit_paths,
            "cracked_blurb": self.cracked_blurb,
            "explanations": self.explanations,
        }


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _mention_ratio(text: str, terms: set[str] | list[str]) -> float:
    blob = text.lower()
    hits = sum(1 for t in terms if t in blob)
    return min(1.0, hits / max(4, len(list(terms)) * 0.15))


def score_item(
    *,
    title: str,
    text: str,
    category: str,
    credibility: float,
    stars: int | None = None,
    comments: int | None = None,
    source_count: int = 1,
    entities: list[str] | None = None,
    settings: Settings | None = None,
) -> ScoreBreakdown:
    settings = settings or get_settings()
    blob = f"{title}\n{text}"
    tokens = tokenize(blob)
    length = len(tokens)

    tech = _mention_ratio(blob, TECH_HINTS)
    weird = _mention_ratio(blob, WEIRD_HINTS)
    depth = _clamp(20 + min(length, 1200) / 20 + tech * 40)
    novelty = _clamp(35 + weird * 45 + (15 if "from scratch" in blob.lower() else 0))
    difficulty = _clamp(30 + tech * 55 + (10 if category in {"BUILD", "DEEP", "MACHINE", "LANG"} else 0))
    originality = _clamp(40 + weird * 40)
    impact = _clamp(25 + min((stars or 0) / 50.0, 25) + min(source_count * 8, 20))
    educational = _clamp(35 + depth * 0.4)
    rarity = _clamp(70 - min((stars or 0) / 80.0, 40) + weird * 20)
    unexpectedness = _clamp(30 + weird * 50 + (15 if category == "WHY" else 0))
    community = _clamp(min(((comments or 0) / 20.0) + ((stars or 0) / 200.0), 1.0) * 100)
    credibility_dim = _clamp(credibility * 100)

    rabbit_paths = [c for c in RABBIT_CONCEPTS if c in blob.lower() or c in (entities or [])]
    if entities:
        for e in entities:
            if e.lower() not in {p.lower() for p in rabbit_paths}:
                rabbit_paths.append(e)
    rabbit_hole = _clamp(20 + len(rabbit_paths) * 8 + depth * 0.25)

    dims = {
        "novelty": novelty,
        "difficulty": difficulty,
        "originality": originality,
        "depth": depth,
        "impact": impact,
        "educational": educational,
        "credibility": credibility_dim,
        "rarity": rarity,
        "unexpectedness": unexpectedness,
        "community": community,
        "rabbit_hole": rabbit_hole,
    }
    weights = settings.scoring_weights()
    total_w = sum(weights.values()) or 1.0
    norm_weights = {k: weights[k] / total_w for k in dims}
    contributions = {k: round(dims[k] * norm_weights[k], 2) for k in dims}
    signal = sum(contributions.values())

    cracked = int(
        round(
            _clamp(
                unexpectedness * 0.28
                + weird * 100 * 0.22
                + difficulty * 0.2
                + novelty * 0.15
                + rabbit_hole * 0.15
            )
        )
    )

    explanations = {
        "novelty": "Weird/from-scratch phrasing and unusual framing.",
        "difficulty": "Dense systems vocabulary and hard categories.",
        "originality": "Rewrite / unnecessary / from-scratch signals.",
        "depth": "Technical density and text length as proxy for substance.",
        "impact": "Cross-source corroboration; stars are capped so popularity cannot dominate.",
        "educational": "How teachable the implementation path looks.",
        "credibility": "Source credibility prior.",
        "rarity": "Obscurity bias — viral stars reduce rarity.",
        "unexpectedness": "Absurd or WHY-desk ambition.",
        "community": "Weak weight for comments/stars (not editorial).",
        "rabbit_hole": "Count of technical concepts / entities opened.",
        "cracked": "Personality blend of unexpectedness, weirdness, difficulty, novelty, rabbit-hole.",
        "popularity_note": "Community/impact weights are intentionally low relative to novelty/difficulty.",
    }

    return ScoreBreakdown(
        dimensions={k: round(v, 2) for k, v in dims.items()},
        contributions=contributions,
        weights={k: round(v, 4) for k, v in norm_weights.items()},
        signal=round(signal, 2),
        cracked=cracked,
        rabbit_hole=round(rabbit_hole, 2),
        rabbit_paths=rabbit_paths[:12],
        cracked_blurb=cracked_blurb(cracked),
        explanations=explanations,
    )


TECH_TAG_MAP = {
    "rust": "Rust",
    "c++": "C++",
    "llvm": "LLVM",
    "webassembly": "WebAssembly",
    "wasm": "WebAssembly",
    "cuda": "CUDA",
    "postgresql": "PostgreSQL",
    "kubernetes": "Kubernetes",
    "python": "Python",
    "typescript": "TypeScript",
    "riscv": "RISC-V",
    "linux kernel": "Linux Kernel",
    "linux": "Linux",
    "react": "React",
    "compiler": "Compilers",
    "networking": "Networking",
    "security": "Security",
    "x86": "x86",
    "arm": "ARM",
    "gpu": "GPU",
    "kernel": "Kernels",
}


def extract_tags(text: str) -> list[str]:
    blob = text.lower()
    tags: list[str] = []
    # Longer keys first so "linux kernel" wins over "linux"
    for key, label in sorted(TECH_TAG_MAP.items(), key=lambda kv: -len(kv[0])):
        if re.search(rf"(?<![a-z]){re.escape(key)}(?![a-z])", blob) and label not in tags:
            tags.append(label)
    if re.search(r"(?<![a-z])c(?![a-z+])", blob) and "C" not in tags:
        tags.append("C")
    return tags[:12]
