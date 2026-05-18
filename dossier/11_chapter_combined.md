# Chapter Combined (adaptive pipeline)

## Purpose
Produce **final chapter prose in one LLM call** by fusing research, write, humanize, edit, and fact-check instructions—used when `chapter_pipeline_mode=auto` selects **combined** (default per-chapter budget).

## Inputs
| Field | Source |
|-------|--------|
| `chapter_number`, `chapter_title`, `chapter_summary`, `target_words`, `genre` | Outline |
| `tone_block` | Memory / `tone_override` (Test C) |
| `memory_context` | memory_read |
| `facts` | RAG retrieval + researcher-style fact list (built in pipeline) |

## Outputs
| Field | Use |
|-------|-----|
| Final chapter prose (all text fields set to same body) | memory_write → assembler |

Agent trace name: `chapter_combined`. Replaces split chain: researcher → writer → humanizer → editor → fact_checker for that chapter.

## Known failure modes
| Failure | Mitigation |
|---------|------------|
| Skipped explicit humanizer pass | Prompt lists all five internal steps + banned AI tells |
| Weaker fact-check vs split | Corpus + “do not invent statistics/ISBNs” in prompt |
| Context overflow | `choose_chapter_pipeline_mode` falls back to **split** |
| Tone override ignored | `tone_override` injected into `tone_block` |

## Why this prompt
- **Token and latency budget**: Assessment-scale books need fewer calls; one strong call beats five cheap ones when context fits.
- **Explicit multi-step instruction**: Models behave better when told to research→write→humanize→edit→verify internally.
- **Same grounding rules as split agents**: Non-fiction abstain rules preserved in one template.
- **Prose-only output**: Avoids JSON truncation on long chapters (unlike batch mode).

## Full prompt
See [prompts/chapter_combined.txt](../prompts/chapter_combined.txt)
