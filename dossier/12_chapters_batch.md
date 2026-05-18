# Chapters Batch (adaptive pipeline)

## Purpose
Write **all chapters in one structured LLM call** when the job is small enough (few chapters, short word targets)—`chapter_pipeline_mode=auto` selects **batch**.

## Inputs
| Field | Source |
|-------|--------|
| `title`, `topic`, `genre` | Outline / brief |
| `tone_block` | Memory |
| `memory_context` | memory_read (chapter 1 context for whole book) |
| `chapter_specs` | Formatted list: number, title, summary, target words per chapter |
| `facts` | Aggregated RAG excerpts per chapter |

## Outputs
| Field | Use |
|-------|-----|
| `ChaptersBatchOutput` JSON `{ chapters: [{chapter_number, title, text}] }` | All chapters updated; per-chapter memory_write |

## Known failure modes
| Failure | Mitigation |
|---------|------------|
| JSON truncation on long books | `batch_chapters_max` + context budget → use combined/split instead |
| Weaker per-chapter memory | Batch uses chapter-1 memory slice; acceptable for short POC runs |
| Inconsistent voice across chapters | Shared `tone_block` and single call |
| Partial chapter failure | Structured output validation; failed parse retries via LLM client |

## Why this prompt
- **Minimum calls for demo/short books**: 1 LLM call for N chapters when N×words fits context.
- **JSON required**: Multiple chapters must return machine-parseable array; unlike combined single-chapter prose mode.
- **Same fused pipeline as combined**: Each chapter still instructed to research→write→humanize→edit→fact-check.
- **Paired with auto mode**: `utils/context_budget.py` only selects batch when safe.

## Full prompt
See [prompts/chapters_batch.txt](../prompts/chapters_batch.txt)
