from __future__ import annotations

import json
from typing import Any

import httpx

from weird.config import Settings
from weird.llm import LLMProvider


class OpenAIProvider(LLMProvider):
    name = "openai"
    mode_label = "cloud_openai"

    def __init__(self, settings: Settings):
        self.settings = settings
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for the OpenAI provider")

    def complete_json(self, prompt_name: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
        payload = {
            "model": self.settings.openai_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are WE-RD's technical editor. Return only valid JSON. Never invent facts.",
                },
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        with httpx.Client(timeout=self.settings.weird_http_timeout) as client:
            response = client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
                json=payload,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
        if isinstance(data, dict):
            data.setdefault("generation_mode", self.mode_label)
        return data
