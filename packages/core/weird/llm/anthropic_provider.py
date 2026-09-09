from __future__ import annotations

import json
from typing import Any

import httpx

from weird.config import Settings
from weird.llm import LLMProvider


class AnthropicProvider(LLMProvider):
    name = "anthropic"
    mode_label = "cloud_anthropic"

    def __init__(self, settings: Settings):
        self.settings = settings
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is required for the Anthropic provider")

    def complete_json(self, prompt_name: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
        payload = {
            "model": self.settings.anthropic_model,
            "max_tokens": 4000,
            "temperature": 0.2,
            "system": "You are WE-RD's technical editor. Return only valid JSON. Never invent facts.",
            "messages": [{"role": "user", "content": prompt}],
        }
        with httpx.Client(timeout=self.settings.weird_http_timeout) as client:
            response = client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            content = response.json()["content"][0]["text"]
        data = json.loads(content)
        if isinstance(data, dict):
            data.setdefault("generation_mode", self.mode_label)
        return data
