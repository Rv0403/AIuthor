"""Token and cost estimation."""
from dataclasses import dataclass

# USD per 1M tokens (approximate, update as pricing changes)
PRICING = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
    "text-embedding-3-small": {"input": 0.02, "output": 0.0},
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
