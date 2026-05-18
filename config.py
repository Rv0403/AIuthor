"""Application configuration."""
from functools import lru_cache
from pathlib import Path
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_AGENT_PROVIDERS = (
    "writer:groq,humanizer:groq,editor:groq,assembler:groq,planner:groq,"
    "intent_analyzer:groq,fact_checker:groq,researcher:groq,tone_eval:groq,"
    "chapter_combined:groq,chapters_batch:groq"
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    groq_api_key: str = ""
    gemini_api_key: str = ""
    langchain_api_key: str = ""
    langchain_tracing_v2: bool = False
    langchain_project: str = "aiuthor"

    cheap_provider: str = "groq"
    strong_provider: str = "groq"
    reasoning_provider: str = "groq"
    grounded_provider: str = "groq"

    groq_cheap_model: str = "llama-3.1-8b-instant"
    groq_strong_model: str = "llama-3.3-70b-versatile"
    gemini_cheap_model: str = "gemini-2.0-flash"
    gemini_strong_model: str = "gemini-2.0-flash"
    gemini_reasoning_model: str = "gemini-2.5-flash"
    gemini_grounded_model: str = "gemini-2.0-flash"

    embedding_model: str = "gemini-embedding-001"
    mock_llm: bool = False

    agent_providers: str = Field(default=DEFAULT_AGENT_PROVIDERS)
    llm_fallback_on_rate_limit: bool = True
    llm_max_retries: int = 2
    llm_retry_base_seconds: float = 2.0
    groq_cheap_max_input_tokens: int = 4500
    groq_strong_max_input_tokens: int = 14000

    humanizer_variants: bool = False
    skip_researcher_without_rag: bool = True
    researcher_use_llm: bool = True
    intent_skip_llm_when_heuristic: bool = False
    auto_run_evals: bool = False

    # auto | batch | combined | split — auto picks from context size
    chapter_pipeline_mode: str = "auto"
    batch_chapters_max: int = 3

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

    def agent_provider_map(self) -> dict[str, str]:
        raw = (self.agent_providers or DEFAULT_AGENT_PROVIDERS).strip()
        return _parse_agent_providers(raw)


def _parse_agent_providers(raw: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for part in raw.split(","):
        part = part.strip()
        if not part or ":" not in part:
            continue
        agent, provider = part.split(":", 1)
        out[agent.strip()] = provider.strip().lower()
    return out


@lru_cache
def get_settings() -> Settings:
    return Settings()
