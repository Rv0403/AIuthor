# Intent Analyzer

## Purpose
Parse natural-language user requests into structured routing fields so LangGraph can branch to generate, tone-convert, insert, export, or repair without separate APIs.

## Inputs
| Field | Source |
|-------|--------|
| `user_input` | API body, Streamlit chat, or CLI |

## Outputs
| Field | Type | Use |
|-------|------|-----|
| `task_type` | enum | Graph routing (`generate_book`, `tone_conversion`, `insert_chapter`, etc.) |
| `topic`, `reader`, `tone`, `genre` | strings | Brief and planner |
| `num_chapters`, `words_per_chapter` | int | Planner / loop bounds |
| `target_chapter` | int or null | Test C regenerate |
| `insert_after`, `source_run_id` | int/string or null | Test D insert |
| `character_names` | list | Fiction planner |

Structured as `IntentResult` JSON (Pydantic).

## Known failure modes
| Failure | Mitigation |
|---------|------------|
| Ambiguous insert position (`insert_after` null or invalid) | `load_source` sets `needs_clarification`; graph ends until user supplies chapter (see dossier/10) |
| Wrong task type on vague input | Few-shot examples in prompt map assessment Tests A–D |
| Missing `source_run_id` for C/D | Heuristic regex + fallback to latest snapshot in `outputs/` |
| LLM unavailable / quota | Optional regex-only path when `MOCK_LLM=true` or `INTENT_SKIP_LLM_WHEN_HEURISTIC=true` |

## Why this prompt
- **Single front door**: Assessment requires one orchestration entry; intent must be machine-readable JSON, not prose.
- **Few-shot routing**: Examples tie assessment phrases (“10 chapter personal finance”, “regenerate chapter 3 academic”, “insert between 4 and 5”) to correct `task_type` without hard-coded parsers for every phrasing.
- **Explicit null for insert**: Example with `insert_after: null` prevents silent default to chapter 4 (Test D integrity).
- **JSON-only**: Enables `invoke_structured` and deterministic graph edges without fragile regex on full books.

## Full prompt
See [prompts/intent_analyzer.txt](../prompts/intent_analyzer.txt)
