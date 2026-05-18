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
    from memory.schemas import (
        BatchChapterItem,
        BookManifest,
        BookOutline,
        ChapterOutline,
        ChapterResearch,
        ChaptersBatchOutput,
        IntentResult,
    )

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
    if schema is ChaptersBatchOutput:
        return ChaptersBatchOutput(
            chapters=[
                BatchChapterItem(chapter_number=1, title="Ch 1", text="Mock chapter one. " * 40),
                BatchChapterItem(chapter_number=2, title="Ch 2", text="Mock chapter two. " * 40),
            ],
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
    raw = _call_llm_resilient(route, prompt, agent, tier=tier, json_mode=True)
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
    raw = _call_llm_resilient(route, prompt, agent, tier=tier, json_mode=False)
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


def _select_route(agent: str, tier: str, *, provider: str | None = None) -> ModelRoute:
    settings = get_settings()
    capability = resolve_capability(agent, tier)

    provider_for_cap = provider or settings.agent_provider_map().get(agent)
    if not provider_for_cap:
        provider_for_cap = {
            "cheap": settings.cheap_provider,
            "strong": settings.strong_provider,
            "reasoning": settings.reasoning_provider,
            "grounded": settings.grounded_provider,
        }.get(capability, settings.cheap_provider)

    return _route_for_provider(provider_for_cap, capability)


def _route_for_provider(provider: str, capability: str) -> ModelRoute:
    settings = get_settings()
    use_grounding = capability == "grounded" and provider == "gemini"

    if provider == "groq":
        # POC: single small model for all agents to stay within free-tier TPM/TPD.
        if capability in ("cheap", "grounded"):
            model = settings.groq_cheap_model
        else:
            model = settings.groq_strong_model
        return ModelRoute("groq", model, use_grounding=False)

    if provider == "gemini":
        model_by_cap = {
            "cheap": settings.gemini_cheap_model,
            "strong": settings.gemini_strong_model,
            "reasoning": settings.gemini_reasoning_model,
            "grounded": settings.gemini_grounded_model,
        }
        return ModelRoute(
            "gemini",
            model_by_cap.get(capability, settings.gemini_strong_model),
            use_grounding,
        )

    raise ValueError(f"Unsupported provider '{provider}' (use groq or gemini)")


def _fallback_route(agent: str, tier: str, failed: ModelRoute) -> ModelRoute | None:
    settings = get_settings()
    if not settings.llm_fallback_on_rate_limit:
        return None
    capability = resolve_capability(agent, tier)
    alt = "gemini" if failed.provider == "groq" else "groq"
    if alt == "groq" and not settings.groq_api_key:
        return None
    if alt == "gemini" and not settings.gemini_api_key:
        return None
    return _route_for_provider(alt, capability)


def _error_text(exc: BaseException) -> str:
    return f"{type(exc).__name__} {exc}".lower()


def _is_transient_error(exc: BaseException) -> bool:
    """503 / overload / timeout — retry or switch model."""
    text = _error_text(exc)
    if any(
        token in text
        for token in (
            "503",
            "502",
            "504",
            "unavailable",
            "high demand",
            "overloaded",
            "timeout",
            "temporarily",
            "servererror",
            "internal",
        )
    ):
        return True
    name = type(exc).__name__.lower()
    return "servererror" in name or "serviceunavailable" in name


def _is_rate_or_quota_error(exc: BaseException) -> bool:
    name = type(exc).__name__.lower()
    if "ratelimit" in name or "resourceexhausted" in name:
        return True
    text = _error_text(exc)
    return (
        "rate limit" in text
        or "rate_limit" in text
        or "quota" in text
        or "429" in text
        or "resource_exhausted" in text
    )


def _is_request_too_large(exc: BaseException) -> bool:
    text = _error_text(exc)
    return (
        "413" in text
        or "request too large" in text
        or "message size" in text
        or ("tokens per minute" in text and "requested" in text)
    )


def _is_recoverable_error(exc: BaseException) -> bool:
    return (
        _is_transient_error(exc)
        or _is_rate_or_quota_error(exc)
        or _is_request_too_large(exc)
    )


def _groq_max_input_tokens(model: str) -> int:
    settings = get_settings()
    cheap = settings.groq_cheap_model
    if model == cheap or "8b" in model.lower():
        return settings.groq_cheap_max_input_tokens
    return settings.groq_strong_max_input_tokens


def _truncate_prompt_to_tokens(prompt: str, max_input_tokens: int) -> str:
    """Keep start + end so instructions and recent prose survive."""
    system_reserve = 120
    budget = max(512, max_input_tokens - system_reserve)
    if estimate_tokens_from_text(prompt) <= budget:
        return prompt
    target_chars = budget * 4
    if len(prompt) <= target_chars:
        return prompt
    head = int(target_chars * 0.45)
    tail = int(target_chars * 0.45)
    marker = "\n\n[... middle truncated for model context limit ...]\n\n"
    return prompt[:head] + marker + prompt[-tail:]


def _degraded_routes(capability: str, prompt: str) -> list[ModelRoute]:
    """Last-resort Groq routes; never send huge chapter prompts to 8b."""
    settings = get_settings()
    if not settings.groq_api_key:
        return []
    est = estimate_tokens_from_text(prompt) + estimate_tokens_from_text(_system_message("agent"))
    routes: list[ModelRoute] = []
    if capability in ("strong", "reasoning"):
        routes.append(_route_for_provider("groq", "strong"))
    if capability in ("cheap", "grounded") and est <= settings.groq_cheap_max_input_tokens - 200:
        routes.append(_route_for_provider("groq", "cheap"))
    elif not routes:
        routes.append(_route_for_provider("groq", "strong"))
    return routes


def _gemini_model_alternates(exclude: str) -> list[str]:
    settings = get_settings()
    candidates = [
        settings.gemini_strong_model,
        settings.gemini_reasoning_model,
        settings.gemini_cheap_model,
        settings.gemini_grounded_model,
        "gemini-2.0-flash",
        "gemini-2.5-flash",
    ]
    seen: set[str] = set()
    out: list[str] = []
    for model in candidates:
        model = model.strip()
        if not model or model == exclude or model in seen:
            continue
        seen.add(model)
        out.append(model)
    return out


def _call_llm_with_retries(
    route: ModelRoute,
    prompt: str,
    agent: str,
    *,
    json_mode: bool,
) -> str:
    settings = get_settings()
    attempts = max(1, settings.llm_max_retries)
    delay = max(0.5, settings.llm_retry_base_seconds)
    last_exc: BaseException | None = None
    working_prompt = prompt

    for attempt in range(attempts):
        try:
            return _call_llm(route, working_prompt, agent, json_mode=json_mode)
        except Exception as exc:
            last_exc = exc
            if _is_request_too_large(exc) and route.provider == "groq":
                cap = _groq_max_input_tokens(route.model)
                shrunk = _truncate_prompt_to_tokens(working_prompt, max(cap // 2, 2048))
                if shrunk != working_prompt:
                    working_prompt = shrunk
                    continue
            if not _is_recoverable_error(exc) or attempt >= attempts - 1:
                raise
            time.sleep(delay * (2**attempt))
    if last_exc:
        raise last_exc
    raise RuntimeError("LLM call failed without exception")


def _call_llm_resilient(
    route: ModelRoute,
    prompt: str,
    agent: str,
    *,
    tier: str,
    json_mode: bool,
) -> str:
    settings = get_settings()
    routes: list[ModelRoute] = [route]

    if route.provider == "gemini":
        for model in _gemini_model_alternates(route.model):
            routes.append(ModelRoute("gemini", model, route.use_grounding))

    alt = _fallback_route(agent, tier, route)
    if alt is not None and alt.provider != route.provider:
        routes.append(alt)
        if alt.provider == "gemini":
            for model in _gemini_model_alternates(alt.model):
                routes.append(ModelRoute("gemini", model, alt.use_grounding))

    capability = resolve_capability(agent, tier)
    routes.extend(_degraded_routes(capability, prompt))

    seen: set[tuple[str, str]] = set()
    last_exc: BaseException | None = None
    for candidate in routes:
        key = (candidate.provider, candidate.model)
        if key in seen:
            continue
        seen.add(key)
        call_prompt = prompt
        if candidate.provider == "groq":
            call_prompt = _truncate_prompt_to_tokens(
                prompt, _groq_max_input_tokens(candidate.model)
            )
        try:
            return _call_llm_with_retries(candidate, call_prompt, agent, json_mode=json_mode)
        except Exception as exc:
            last_exc = exc
            if not _is_recoverable_error(exc):
                raise
    if last_exc:
        raise last_exc
    raise RuntimeError("No LLM route available")


def _system_message(agent: str) -> str:
    return f"You are the {agent} agent for AIuthor book generation. Follow instructions precisely."


def _call_groq(model: str, prompt: str, agent: str, *, json_mode: bool) -> str:
    settings = get_settings()
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY required for Groq models")
    from openai import OpenAI

    system = _system_message(agent)
    max_in = _groq_max_input_tokens(model)
    user_content = _truncate_prompt_to_tokens(prompt, max_in - estimate_tokens_from_text(system))

    client = OpenAI(api_key=settings.groq_api_key, base_url="https://api.groq.com/openai/v1")
    settings = get_settings()
    max_out = 8192
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.7,
        "max_tokens": max_out,
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


def _call_llm(route: ModelRoute, prompt: str, agent: str, *, json_mode: bool) -> str:
    if route.provider == "groq":
        return _call_groq(route.model, prompt, agent, json_mode=json_mode)
    if route.provider == "gemini":
        return _call_gemini(
            route.model, prompt, agent, json_mode=json_mode, use_grounding=route.use_grounding
        )
    raise ValueError(f"Unknown provider: {route.provider} (use groq or gemini)")


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

