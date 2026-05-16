# Intent Analyzer Agent

## Purpose
Parse natural-language user requests into structured task types for LangGraph routing.

## Inputs
- `user_input` (string)

## Outputs
- `IntentResult` JSON: task_type, topic, tone, num_chapters, target_chapter, insert_after, source_run_id

## Failure Modes
- Ambiguous insert position → defaults insert_after=4
- Missing source run for C/D → falls back to latest run in outputs/

## Prompt Logic
Few-shot examples in prompt map assessment Tests A–D to task types; heuristics reinforce when MOCK_LLM enabled.

## Full Prompt
See [prompts/intent_analyzer.txt](../prompts/intent_analyzer.txt)
