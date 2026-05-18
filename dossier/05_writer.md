# Writer

## Purpose
Generate the first full draft of a chapter from outline, memory, grounded facts, and tone rules.

## Inputs
| Field | Source |
|-------|--------|
| `chapter_number`, `chapter_title`, `chapter_summary`, `target_words`, `genre` | Outline |
| `tone_block` | Memory `tone_fingerprint` (from tonality preset) |
| `memory_context` | Callbacks, prior facts, characters |
| `facts` | Researcher / RAG |

Used in **split** pipeline mode only (`chapter_pipeline` → `split`).

## Outputs
| Field | Use |
|-------|-----|
| `raw_text` | Humanizer input |

## Known failure modes
| Failure | Mitigation |
|---------|------------|
| Repetitive openings | Humanizer + optional preference-lite opening judge |
| Ungrounded non-fiction claims | Prompt: only use facts list; fact_checker later |
| AI tells in draft | Explicit banned-phrase list; humanizer enforces harder |
| Wrong tone | `tone_block` + tonality presets |
| Fiction character drift | Character bible in memory_context |

## Why this prompt
- **Draft-only contract**: Writer optimizes for coverage and structure; polish delegated to humanizer/editor—clear agent boundary for assessment.
- **Memory-aware**: Callbacks listed explicitly so chapters reference prior material (continuity requirement).
- **Genre split**: Non-fiction grounded vs fiction character rules in one template.
- **Prose-only output**: No JSON—reduces schema errors on long chapters.

## Full prompt
See [prompts/writer.txt](../prompts/writer.txt)
