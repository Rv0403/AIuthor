"""Per-agent LLM capability routing (Groq text + Gemini embeddings by default)."""
from __future__ import annotations

# Capability: cheap | strong | reasoning | grounded
AGENT_CAPABILITIES: dict[str, str] = {
    "intent_analyzer": "cheap",
    "planner": "reasoning",
    "researcher": "grounded",
    "writer": "strong",
    "humanizer": "strong",
    "editor": "strong",
    "fact_checker": "cheap",
    "assembler": "strong",
    "tone_eval": "cheap",
}

TIER_FALLBACK: dict[str, str] = {
    "cheap": "cheap",
    "strong": "strong",
}


def resolve_capability(agent: str, tier: str) -> str:
    return AGENT_CAPABILITIES.get(agent, TIER_FALLBACK.get(tier, "cheap"))
