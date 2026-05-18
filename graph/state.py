"""LangGraph state definition."""
from __future__ import annotations

from typing import Any, TypedDict


class BookState(TypedDict, total=False):
    user_input: str
    run_id: str
    task_type: str
    intent: dict[str, Any]
    brief: dict[str, Any]
    outline: dict[str, Any]
    current_chapter: int
    total_chapters: int
    research_by_chapter: dict[int, dict[str, Any]]
    chapters: list[dict[str, Any]]
    memory: dict[str, Any]
    manifest: dict[str, Any]
    output_paths: dict[str, str]
    traces: list[dict[str, Any]]
    errors: list[str]
    source_run_id: str | None
    insert_after: int | None
    target_chapter: int | None
    tone_override: str | None
    status: str
    clarification_message: str | None
    pending_insert: dict[str, Any] | None
    chapter_pipeline_mode: str
