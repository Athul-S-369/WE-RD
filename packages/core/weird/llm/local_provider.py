from __future__ import annotations

import json
from typing import Any

import httpx

from weird.config import Settings
from weird.llm import LLMProvider


class LocalProvider(LLMProvider):
    name = "local"
    mode_label = "local_llm"

    def __init__(self, settings: Settings):
        self.settings = settings
        if not settings.weird_local_llm_url:
            raise RuntimeError("WEIRD_LOCAL_LLM_URL is required for the local provider")

    def complete_json(self, prompt_name: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
        payload = {
            "model": self.settings.weird_local_llm_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are WE-RD's technical editor. Return only valid JSON. Never invent facts.",
                },
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
        with httpx.Client(timeout=max(self.settings.weird_http_timeout, 60)) as client:
            response = client.post(self.settings.weird_local_llm_url, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data.get("message", {}).get("content") or data.get("choices", [{}])[0].get(
                "message", {}
            ).get("content")
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            parsed.setdefault("generation_mode", self.mode_label)
        return parsed
