"""Observability: agent traces, prompt logs, memory I/O, token ledger."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import get_settings


class TraceLogger:
    def __init__(self, run_id: str):
        settings = get_settings()
        self.run_id = run_id
        self.base = settings.traces_dir / run_id
        self.base.mkdir(parents=True, exist_ok=True)
        self._prompt_log = self.base / "prompt_log.jsonl"
        self._agent_trace = self.base / "agent_trace.jsonl"
        self._memory_io = self.base / "memory_io.jsonl"
        self._token_ledger = self.base / "token_ledger.jsonl"

    def _append(self, path: Path, record: dict[str, Any]) -> None:
        record["timestamp"] = datetime.now(timezone.utc).isoformat()
        record["run_id"] = self.run_id
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def log_agent_start(self, agent: str, inputs: dict[str, Any]) -> None:
        self._append(
            self._agent_trace,
            {"event": "start", "agent": agent, "inputs_summary": _summarize(inputs)},
        )

    def log_agent_end(self, agent: str, outputs: dict[str, Any], duration_ms: float = 0) -> None:
        self._append(
            self._agent_trace,
            {
                "event": "end",
                "agent": agent,
                "outputs_summary": _summarize(outputs),
                "duration_ms": duration_ms,
            },
        )

    def log_prompt(
        self,
        agent: str,
        prompt: str,
        response: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        from utils.token_tracker import TokenUsage

        usage = TokenUsage(input_tokens, output_tokens, model)
        cost = usage.estimate_cost_usd()
        self._append(
            self._prompt_log,
            {
                "agent": agent,
                "model": model,
                "prompt": prompt[:8000],
                "response": response[:8000],
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": round(cost, 6),
            },
        )
        self._append(
            self._token_ledger,
            {
                "agent": agent,
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost_usd": round(cost, 6),
            },
        )

    def log_memory_io(
        self,
        agent: str,
        operation: str,
        memory_read: list[str] | None = None,
        memory_write: list[str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self._append(
            self._memory_io,
            {
                "agent": agent,
                "operation": operation,
                "memory_read": memory_read or [],
                "memory_write": memory_write or [],
                "details": details or {},
            },
        )


_loggers: dict[str, TraceLogger] = {}


def get_trace_logger(run_id: str) -> TraceLogger:
    if run_id not in _loggers:
        _loggers[run_id] = TraceLogger(run_id)
    return _loggers[run_id]


def _summarize(data: dict[str, Any], max_len: int = 500) -> str:
    s = json.dumps(data, default=str)
    return s[:max_len] + ("..." if len(s) > max_len else "")
