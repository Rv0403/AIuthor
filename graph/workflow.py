"""LangGraph workflow — orchestrator with conditional routing."""
from __future__ import annotations

import uuid
from typing import Any


def _patch_langchain_reviver_default() -> None:
    """LangGraph's serde uses Reviver() with allowed_objects=None, which warns on every import."""
    import importlib

    lc_load = importlib.import_module("langchain_core.load.load")
    if getattr(lc_load.Reviver, "_aiuthor_default_core", False):
        return

    _orig = lc_load.Reviver

    class Reviver(_orig):  # type: ignore[misc, valid-type]
        _aiuthor_default_core = True

        def __init__(self, allowed_objects="core", **kwargs):  # type: ignore[no-untyped-def]
            super().__init__(allowed_objects=allowed_objects, **kwargs)

    lc_load.Reviver = Reviver


_patch_langchain_reviver_default()

from langgraph.graph import END, StateGraph

from graph.nodes import (
    node_advance_chapter,
    node_assembler,
    node_chapter_pipeline,
    node_init_generate,
    node_intent,
    node_load_source,
    node_planner,
    node_prepare_insert,
)
from graph.routing import (
    route_after_chapter_pipeline,
    route_after_intent,
    route_after_load,
    should_continue_chapters,
)
from graph.state import BookState
from config import get_settings


def build_workflow():
    graph = StateGraph(BookState)

    graph.add_node("intent", node_intent)
    graph.add_node("load_source", node_load_source)
    graph.add_node("prepare_insert", node_prepare_insert)
    graph.add_node("init_generate", node_init_generate)
    graph.add_node("planner", node_planner)
    graph.add_node("chapter_pipeline", node_chapter_pipeline)
    graph.add_node("advance_chapter", node_advance_chapter)
    graph.add_node("assembler", node_assembler)

    graph.set_entry_point("intent")

    graph.add_conditional_edges("intent", route_after_intent, {
        "planner": "init_generate",
        "load_source": "load_source",
    })

    graph.add_edge("init_generate", "planner")

    graph.add_conditional_edges("load_source", route_after_load, {
        "planner": "planner",
        "chapter_pipeline": "chapter_pipeline",
        "prepare_insert": "prepare_insert",
        "assembler": "assembler",
        "needs_clarification": END,
    })

    graph.add_edge("prepare_insert", "chapter_pipeline")

    graph.add_conditional_edges("planner", should_continue_chapters, {
        "chapter_loop": "chapter_pipeline",
        "assembler": "assembler",
    })

    graph.add_conditional_edges("chapter_pipeline", route_after_chapter_pipeline, {
        "advance_chapter": "advance_chapter",
        "assembler": "assembler",
    })

    graph.add_conditional_edges("advance_chapter", should_continue_chapters, {
        "chapter_loop": "chapter_pipeline",
        "assembler": "assembler",
    })

    graph.add_edge("assembler", END)

    return graph.compile()


def run_workflow(
    user_input: str,
    run_id: str | None = None,
    *,
    task_type: str | None = None,
    insert_after: int | None = None,
    source_run_id: str | None = None,
    intent: dict[str, Any] | None = None,
    brief: dict[str, Any] | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    settings.outputs_dir.mkdir(parents=True, exist_ok=True)
    settings.traces_dir.mkdir(parents=True, exist_ok=True)

    rid = run_id or str(uuid.uuid4())[:12]
    from utils.logger import get_trace_logger

    get_trace_logger(rid)

    app = build_workflow()
    initial: BookState = {
        "user_input": user_input,
        "run_id": rid,
        "chapters": [],
        "research_by_chapter": {},
        "memory": {},
        "errors": [],
        "status": "running",
    }
    if task_type:
        initial["task_type"] = task_type
    if insert_after is not None:
        initial["insert_after"] = insert_after
    if source_run_id:
        initial["source_run_id"] = source_run_id
    if intent:
        initial["intent"] = intent
    if brief:
        initial["brief"] = brief

    result = app.invoke(initial)
    return dict(result)
