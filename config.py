"""Application configuration."""
from pathlib import Path
from functools import lru_cache
from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    groq_api_key: str = ""
    gemini_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    langchain_api_key: str = ""
    langchain_tracing_v2: bool = False
    langchain_project: str = "aiuthor"

    # groq_gemini (default) | ollama | openai
    llm_provider: str = "groq_gemini"

    cheap_provider: str = "groq"
    strong_provider: str = "groq"
    reasoning_provider: str = "gemini"
    grounded_provider: str = "gemini"

    groq_cheap_model: str = "llama-3.1-8b-instant"
    groq_strong_model: str = "llama-3.3-70b-versatile"
    gemini_cheap_model: str = "gemini-2.0-flash"
    gemini_strong_model: str = "gemini-2.0-flash"
    gemini_reasoning_model: str = "gemini-2.5-flash"
    gemini_grounded_model: str = "gemini-2.0-flash"

    ollama_base_url: str = "http://localhost:11434"
    ollama_strong_model: str = "llama3.2"
    ollama_cheap_model: str = "llama3.2"

    openai_strong_model: str = "gpt-4o"
    openai_cheap_model: str = "gpt-4o-mini"
    anthropic_strong_model: str = "claude-sonnet-4-20250514"
    anthropic_cheap_model: str = "claude-3-5-haiku-20241022"

    embedding_provider: str = "gemini"
    embedding_model: str = "text-embedding-004"

    mock_llm: bool = False

    project_root: Path = Path(__file__).parent
    outputs_dir: Path = project_root / "outputs"
    traces_dir: Path = project_root / "traces"
    chroma_dir: Path = project_root / ".chroma"
    prompts_dir: Path = project_root / "prompts"
    rag_corpus_dir: Path = project_root / "rag" / "corpus"

    chunk_size: int = 1000
    chunk_overlap: int = 200
    rag_top_k: int = 5

    @model_validator(mode="after")
    def _load_legacy_env_key_names(self) -> Self:
        import os

        if not self.groq_api_key:
            self.groq_api_key = (
                os.environ.get("GROQ_API_KEY", "")
                or os.environ.get("grok_api_key", "")
                or os.environ.get("GROK_API_KEY", "")
            )
        if not self.gemini_api_key:
            self.gemini_api_key = os.environ.get("GEMINI_API_KEY", "") or os.environ.get(
                "gemini_api_key", ""
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
