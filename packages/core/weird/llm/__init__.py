from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from weird.config import Settings, get_settings


class LLMProvider(ABC):
    name: str
    mode_label: str = "unknown"

    @abstractmethod
    def complete_json(self, prompt_name: str, prompt: str, **kwargs: Any) -> dict[str, Any]:
        raise NotImplementedError


def get_provider(settings: Settings | None = None) -> LLMProvider:
    settings = settings or get_settings()
    provider = settings.weird_llm_provider
    if provider == "openai":
        if not settings.openai_api_key:
            return _fallback_mock(settings, "openai key missing")
        from weird.llm.openai_provider import OpenAIProvider

        return OpenAIProvider(settings)
    if provider == "anthropic":
        if not settings.anthropic_api_key:
            return _fallback_mock(settings, "anthropic key missing")
        from weird.llm.anthropic_provider import AnthropicProvider

        return AnthropicProvider(settings)
    if provider == "gemini":
        if not settings.gemini_api_key:
            return _fallback_mock(settings, "gemini key missing")
        from weird.llm.gemini_provider import GeminiProvider

        return GeminiProvider(settings)
    if provider == "local":
        if not settings.weird_local_llm_url:
            return _fallback_mock(settings, "local llm url missing")
        from weird.llm.local_provider import LocalProvider

        return LocalProvider(settings)
    from weird.llm.mock_provider import MockProvider

    return MockProvider(settings)


def _fallback_mock(settings: Settings, reason: str) -> LLMProvider:
    from weird.llm.mock_provider import MockProvider

    provider = MockProvider(settings)
    provider.mode_label = f"deterministic_fallback ({reason})"
    return provider


def provider_status(settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    provider = get_provider(settings)
    return {
        "configured": settings.weird_llm_provider,
        "active": provider.name,
        "mode_label": getattr(provider, "mode_label", provider.name),
        "honest": True,
    }
