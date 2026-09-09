from __future__ import annotations

import os
from pathlib import Path


def prompts_dir() -> Path:
    """Resolve prompt templates for both editable installs and wheels."""
    env = os.environ.get("WEIRD_PROMPTS_DIR")
    if env:
        path = Path(env)
        if path.is_dir():
            return path

    here = Path(__file__).resolve()
    candidates = [
        here.parent.parent / "prompts",  # packages/core/weird/prompts (packaged)
        here.parents[3] / "prompts",  # monorepo packages/prompts
        Path("/app/packages/prompts"),
    ]
    for candidate in candidates:
        if candidate.is_dir() and any(candidate.glob("*.txt")):
            return candidate
    raise FileNotFoundError(
        "WE-RD prompt templates not found. Expected packages/core/weird/prompts "
        "or set WEIRD_PROMPTS_DIR."
    )


def load_prompt(name: str) -> str:
    path = prompts_dir() / f"{name}.txt"
    return path.read_text(encoding="utf-8")


def render_prompt(name: str, **kwargs: str) -> str:
    template = load_prompt(name)
    for key, value in kwargs.items():
        template = template.replace("{{" + key + "}}", value)
    return template
