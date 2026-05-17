"""Token and cost estimation."""
from dataclasses import dataclass

# USD per 1M tokens (approximate, update as pricing changes)
PRICING = {
    "llama-3.3-70b-versatile": {"input": 0.0, "output": 0.0},
    "llama-3.1-8b-instant": {"input": 0.0, "output": 0.0},
    "gemini-2.0-flash": {"input": 0.0, "output": 0.0},
    "gemini-2.5-flash": {"input": 0.0, "output": 0.0},
    "gemini-embedding-001": {"input": 0.0, "output": 0.0},
}


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def estimate_cost_usd(self) -> float:
        rates = PRICING.get(self.model, {"input": 1.0, "output": 3.0})
        return (self.input_tokens * rates["input"] + self.output_tokens * rates["output"]) / 1_000_000


def estimate_tokens_from_text(text: str) -> int:
    return max(1, len(text) // 4)
