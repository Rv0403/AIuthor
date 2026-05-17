"""Conditional routing for LangGraph."""
from graph.state import BookState


def route_after_intent(state: BookState) -> str:
    task = state.get("task_type", "generate_book")
    mapping = {
        "generate_book": "planner",
        "tone_conversion": "load_source",
        "insert_chapter": "load_source",
        "export_book": "load_source",
        "repair_book": "load_source",
        "regenerate_chapter": "load_source",
    }
    return mapping.get(task, "planner")


def route_after_load(state: BookState) -> str:
    if state.get("status") == "needs_clarification":
        return "needs_clarification"
    task = state.get("task_type", "")
    if task == "tone_conversion":
        return "chapter_pipeline"
    if task == "insert_chapter":
        return "prepare_insert"
    if task in ("export_book", "repair_book"):
        return "assembler"
    return "planner"


def should_continue_chapters(state: BookState) -> str:
    current = state.get("current_chapter", 1)
    total = state.get("total_chapters", 1)
    if current <= total:
        return "chapter_loop"
    return "assembler"


def route_after_chapter_pipeline(state: BookState) -> str:
    task = state.get("task_type", "generate_book")
    if task in ("tone_conversion", "insert_chapter", "regenerate_chapter"):
        return "assembler"
    return "advance_chapter"
