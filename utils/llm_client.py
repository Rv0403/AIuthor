"""LLM invocation with structured outputs and Groq/Gemini capability routing."""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any, TypeVar

from pydantic import BaseModel

from config import get_settings
from utils.model_routing import resolve_capability
from utils.token_tracker import estimate_tokens_from_text

T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True)
class ModelRoute:
    provider: str
    model: str
    use_grounding: bool = False


def load_prompt(name: str, **kwargs: str) -> str:
    settings = get_settings()
    path = settings.prompts_dir / name
    if not path.exists():
        path = settings.prompts_dir / f"{name}.txt"
    text = path.read_text(encoding="utf-8")
    for key, val in kwargs.items():
        text = text.replace(f"{{{{{key}}}}}", val)
    return text


def _mock_response(schema: type[T], agent: str) -> T:
    """Deterministic mock for offline tests."""
    from memory.schemas import BookOutline, ChapterOutline, IntentResult, BookManifest, ChapterResearch

    if schema is IntentResult:
        return IntentResult(
            task_type="generate_book",
            topic="Personal Finance",
            reader="Beginners",
            tone="Conversational",
            num_chapters=2,
            words_per_chapter=400,
        )  # type: ignore
    if schema is BookOutline:
        return BookOutline(
            title="Money Made Simple",
            chapters=[
                ChapterOutline(chapter_number=1, title="Understanding Money", summary="Financial mindset basics", target_words=400),
                ChapterOutline(chapter_number=2, title="Saving Smart", summary="Building your first emergency fund", target_words=400),
            ],
        )  # type: ignore
    if schema is ChapterResearch:
        return ChapterResearch(
            chapter_number=1,
            facts=[{"fact": "Emergency funds cover 3-6 months of expenses", "source": "personal_finance_basics.txt"}],
            references=["General budgeting principles"],
            glossary_candidates=[{"term": "Emergency fund", "definition": "Cash set aside for surprises"}],
        )  # type: ignore
    if schema is BookManifest:
        return BookManifest(
            title="Money Made Simple",
            half_title="Money Made Simple",
            copyright_block="Copyright placeholder",
            dedication="For every beginner.",
            epigraph="Start where you are.",
            foreword="Welcome.",
            preface="You can do this.",
            acknowledgments="Thanks to readers.",
            introduction="Let's talk money.",
            afterword="Keep going.",
            appendix="Worksheets placeholder.",
            about_author="Written with AIuthor.",
            back_cover_copy="Your guide to simpler money.",
        )  # type: ignore
    data: dict[str, Any] = {}
    for name, field in schema.model_fields.items():
        ann = str(field.annotation)
        if "list" in ann.lower():
            data[name] = []
        elif "int" in ann.lower():
            data[name] = 1
        elif "str" in ann.lower():
            data[name] = f"mock_{agent}_{name}"
        else:
            data[name] = None
    return schema.model_validate(data)


def invoke_structured(
    agent: str,
    prompt: str,
    schema: type[T],
    *,
    tier: str = "cheap",
    run_id: str = "",
) -> T:
    settings = get_settings()
    trace = None
    if run_id:
        from utils.logger import get_trace_logger

        trace = get_trace_logger(run_id)

    if settings.mock_llm:
        result = _mock_response(schema, agent)
        if trace:
            trace.log_prompt(agent, prompt, result.model_dump_json(), "mock", 100, 200)
        return result

    route = _select_route(agent, tier)
    start = time.perf_counter()
    raw = _call_llm(route, prompt, agent, json_mode=True)
    duration_ms = (time.perf_counter() - start) * 1000

    parsed = _parse_json_response(raw, schema)
    in_tok = estimate_tokens_from_text(prompt)
    out_tok = estimate_tokens_from_text(raw)

    if trace:
        trace.log_prompt(agent, prompt, raw, f"{route.provider}:{route.model}", in_tok, out_tok)
        trace.log_agent_end(agent, parsed.model_dump(), duration_ms)

    return parsed


def invoke_text(
    agent: str,
    prompt: str,
    *,
    tier: str = "strong",
    run_id: str = "",
) -> str:
    settings = get_settings()
    if settings.mock_llm:
        return f"[Mock output for {agent}]\n\n" + ("Sample prose. " * 80)

    route = _select_route(agent, tier)
    raw = _call_llm(route, prompt, agent, json_mode=False)
    if run_id:
        from utils.logger import get_trace_logger

        trace = get_trace_logger(run_id)
        trace.log_prompt(
            agent,
            prompt,
            raw,
            f"{route.provider}:{route.model}",
            estimate_tokens_from_text(prompt),
            estimate_tokens_from_text(raw),
        )
    return raw


def _select_route(agent: str, tier: str) -> ModelRoute:
    settings = get_settings()
    capability = resolve_capability(agent, tier)

    if settings.llm_provider == "ollama":
        model = (
            settings.ollama_strong_model
            if capability in ("strong", "reasoning")
            else settings.ollama_cheap_model
        )
        return ModelRoute("ollama", model, use_grounding=False)

    if settings.llm_provider == "openai" and settings.openai_api_key:
        model = settings.openai_strong_model if capability != "cheap" else settings.openai_cheap_model
        return ModelRoute("openai", model, use_grounding=False)

    if settings.llm_provider == "anthropic" and settings.anthropic_api_key:
        model = (
            settings.anthropic_strong_model if capability != "cheap" else settings.anthropic_cheap_model
        )
        return ModelRoute("anthropic", model, use_grounding=False)

    provider_for_cap = {
        "cheap": settings.cheap_provider,
        "strong": settings.strong_provider,
        "reasoning": settings.reasoning_provider,
        "grounded": settings.grounded_provider,
    }.get(capability, settings.cheap_provider)

    use_grounding = capability == "grounded" and provider_for_cap == "gemini"

    if provider_for_cap == "groq":
        model = settings.groq_cheap_model if capability == "cheap" else settings.groq_strong_model
        return ModelRoute("groq", model, use_grounding=False)

    if provider_for_cap == "gemini":
        model_by_cap = {
            "cheap": settings.gemini_cheap_model,
            "strong": settings.gemini_strong_model,
            "reasoning": settings.gemini_reasoning_model,
            "grounded": settings.gemini_grounded_model,
        }
        return ModelRoute("gemini", model_by_cap.get(capability, settings.gemini_strong_model), use_grounding)

    raise ValueError(f"Unsupported provider '{provider_for_cap}' for agent '{agent}'")


def _system_message(agent: str) -> str:
    return f"You are the {agent} agent for AIuthor book generation. Follow instructions precisely."


def _call_groq(model: str, prompt: str, agent: str, *, json_mode: bool) -> str:
    settings = get_settings()
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY required for Groq models")
    from openai import OpenAI

    client = OpenAI(api_key=settings.groq_api_key, base_url="https://api.groq.com/openai/v1")
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": _system_message(agent)},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content or ""


def _call_gemini(model: str, prompt: str, agent: str, *, json_mode: bool, use_grounding: bool) -> str:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY required for Gemini models")
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.gemini_api_key)
    config_kwargs: dict[str, Any] = {
        "system_instruction": _system_message(agent),
        "temperature": 0.7,
        "max_output_tokens": 8192,
    }
    if json_mode:
        config_kwargs["response_mime_type"] = "application/json"
    if use_grounding:
        config_kwargs["tools"] = [types.Tool(google_search=types.GoogleSearch())]

    resp = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(**config_kwargs),
    )
    return (resp.text or "").strip()


def _call_ollama(model: str, prompt: str, agent: str) -> str:
    import httpx

    settings = get_settings()
    url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"
    resp = httpx.post(
        url,
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": _system_message(agent)},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        },
        timeout=600.0,
    )
    resp.raise_for_status()
    return resp.json().get("message", {}).get("content", "")


def _call_openai_legacy(model: str, prompt: str, agent: str) -> str:
    settings = get_settings()
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _system_message(agent)},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )
    return resp.choices[0].message.content or ""


def _call_anthropic_legacy(model: str, prompt: str, agent: str) -> str:
    settings = get_settings()
    from anthropic import Anthropic

    client = Anthropic(api_key=settings.anthropic_api_key)
    resp = client.messages.create(
        model=model,
        max_tokens=8192,
        system=_system_message(agent),
        messages=[{"role": "user", "content": prompt}],
    )
    blocks = [b.text for b in resp.content if hasattr(b, "text")]
    return "\n".join(blocks)


def _call_llm(route: ModelRoute, prompt: str, agent: str, *, json_mode: bool) -> str:
    if route.provider == "groq":
        return _call_groq(route.model, prompt, agent, json_mode=json_mode)
    if route.provider == "gemini":
        return _call_gemini(
            route.model, prompt, agent, json_mode=json_mode, use_grounding=route.use_grounding
        )
    if route.provider == "ollama":
        return _call_ollama(route.model, prompt, agent)
    if route.provider == "openai":
        return _call_openai_legacy(route.model, prompt, agent)
    if route.provider == "anthropic":
        return _call_anthropic_legacy(route.model, prompt, agent)
    raise ValueError(f"Unknown provider: {route.provider}")


def _parse_json_response(raw: str, schema: type[T]) -> T:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(text[start:end])
        else:
            raise
    return schema.model_validate(data)
