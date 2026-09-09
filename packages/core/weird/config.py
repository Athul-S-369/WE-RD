from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://weird:weird@localhost:5432/weird"
    weird_api_host: str = "0.0.0.0"
    weird_api_port: int = 8000
    weird_cors_origins: str = "http://localhost:3000"
    weird_admin_token: str = "change-me-in-production"
    weird_demo_mode: bool = True
    weird_log_level: str = "INFO"

    weird_llm_provider: Literal["mock", "openai", "anthropic", "gemini", "local"] = "mock"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    weird_local_llm_url: str = ""
    weird_local_llm_model: str = "llama3.1"

    # Embeddings / vector store
    weird_embedding_backend: Literal["auto", "hashed", "sentence-transformers"] = "auto"
    weird_local_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    weird_use_pgvector: bool = False

    github_token: str = ""
    youtube_api_key: str = ""

    weird_weight_novelty: float = 1.2
    weird_weight_difficulty: float = 1.3
    weird_weight_originality: float = 1.1
    weird_weight_depth: float = 1.2
    weird_weight_impact: float = 0.7
    weird_weight_educational: float = 1.0
    weird_weight_credibility: float = 0.9
    weird_weight_rarity: float = 1.1
    weird_weight_unexpectedness: float = 1.2
    weird_weight_community: float = 0.35
    weird_weight_rabbit_hole: float = 1.15

    weird_max_llm_candidates: int = 40
    weird_http_timeout: float = 20.0
    weird_explore_sources: bool = True
    weird_explore_max_per_story: int = 2

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.weird_cors_origins.split(",") if o.strip()]

    def scoring_weights(self) -> dict[str, float]:
        return {
            "novelty": self.weird_weight_novelty,
            "difficulty": self.weird_weight_difficulty,
            "originality": self.weird_weight_originality,
            "depth": self.weird_weight_depth,
            "impact": self.weird_weight_impact,
            "educational": self.weird_weight_educational,
            "credibility": self.weird_weight_credibility,
            "rarity": self.weird_weight_rarity,
            "unexpectedness": self.weird_weight_unexpectedness,
            "community": self.weird_weight_community,
            "rabbit_hole": self.weird_weight_rabbit_hole,
        }

    def processing_mode(self) -> dict[str, str | bool]:
        """Honest labels for what intelligence path is active."""
        llm = self.weird_llm_provider
        if llm == "openai" and not self.openai_api_key:
            llm = "mock (openai key missing)"
        if llm == "anthropic" and not self.anthropic_api_key:
            llm = "mock (anthropic key missing)"
        if llm == "gemini" and not self.gemini_api_key:
            llm = "mock (gemini key missing)"
        if llm == "local" and not self.weird_local_llm_url:
            llm = "mock (local llm url missing)"
        return {
            "llm": llm,
            "embeddings": self.weird_embedding_backend,
            "pgvector": self.weird_use_pgvector,
            "github_token": bool(self.github_token),
            "youtube_api": bool(self.youtube_api_key),
            "demo_mode": self.weird_demo_mode,
            "zero_key": not any(
                [self.openai_api_key, self.anthropic_api_key, self.gemini_api_key, self.weird_local_llm_url]
            )
            and self.weird_llm_provider in {"mock", "openai", "anthropic", "gemini", "local"},
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
