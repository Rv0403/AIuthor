# Intent Analyzer Agent

## Purpose
Parse natural-language user requests into structured task types for LangGraph routing.

## Inputs
- `user_input` (string)

## Outputs
- `IntentResult` JSON: task_type, topic, tone, num_chapters, target_chapter, insert_after, source_run_id

## Failure Modes
- Ambiguous insert position (`insert_after` null or out of range) → `load_source` sets `status: needs_clarification` and ends the graph; no silent default to chapter 4
- Streamlit chat (same thread) asks for a chapter number; user reply parsed by `agents/insert_clarification.py` (`parse_insert_after`, `validate_insert_after`)
- Resume: second `run_workflow` call with `task_type=insert_chapter`, `insert_after`, `source_run_id` (intent node pass-through skips re-parse)
- API: `POST /execute` returns `clarification_message` and `pending_insert`; client may retry with `insert_after` in the body
- Missing source run for C/D → falls back to latest run in outputs/

## Prompt Logic
Few-shot examples in prompt map assessment Tests A–D to task types; explicit example for insert without position (`insert_after: null`). Heuristics reinforce when MOCK_LLM enabled.

## Full Prompt
See [prompts/intent_analyzer.txt](../prompts/intent_analyzer.txt)
