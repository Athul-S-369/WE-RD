from __future__ import annotations

import json
from typing import Any

import httpx

from weird.config import Settings
from weird.llm import LLMProvider


class GeminiProvider(LLMProvider):
    name = "gemini"
    mode_label = "cloud_gemini"

    def __init__(self, settings: Settings):
        self.settings = settings

    def complete_json(self, prompt_name: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
        if not self.settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY not configured")
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.settings.gemini_model}:generateContent"
        )
        body = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                "Return ONLY valid JSON for the WE-RD newspaper pipeline. "
                                "Do not invent benchmarks, video IDs, or unsupported facts.\n\n"
                                + prompt
                            )
                        }
                    ],
                }
            ],
            "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
        }
        with httpx.Client(timeout=self.settings.weird_http_timeout) as client:
            response = client.post(url, params={"key": self.settings.gemini_api_key}, json=body)
            response.raise_for_status()
            data = response.json()
        text = (
            ((data.get("candidates") or [{}])[0].get("content") or {}).get("parts") or [{}]
        )[0].get("text") or "{}"
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            parsed.setdefault("generation_mode", self.mode_label)
            return parsed
        return {"value": parsed, "generation_mode": self.mode_label}
