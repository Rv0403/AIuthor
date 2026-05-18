# Memory Keeper

## Purpose
Persist cross-chapter continuity—facts, callbacks, glossary, character bible, tone fingerprint, decision log—and expose relevant slices to downstream prompts. Not an LLM agent; deterministic read/write around `BookMemory`.

## Inputs
| Phase | Fields |
|-------|--------|
| **Read** (`memory_read`) | `run_id`, `current_chapter`, existing `BookMemory` |
| **Write** (`memory_write`) | `research_by_chapter`, verified chapter text, `outline`, `chapters`, `brief` |

Tone fingerprint loaded from tonality preset files (see dossier/14).

## Outputs
| Field | Use |
|-------|-----|
| Updated `BookMemory` on disk (`outputs/{run_id}/memory.json`) | Next chapter prompts |
| `snapshot.json` | Resume, tone_conversion, insert_chapter |
| Trace `memory_io.jsonl` | Observability |

## Known failure modes
| Failure | Mitigation |
|---------|------------|
| Callback spam | Only first 120 chars of chapter stored as callback seed |
| Stale facts after insert | `repair.py` renumbers refs before write (after valid `insert_after`; see dossier/10) |
| Missing tone preset file | Defaults to generic rule list |
| Context bloat | `format_memory_context` caps callbacks/facts sent to prompts |

## Why this prompt (tonality presets, not LLM)
Memory Keeper has **no** `prompts/memory_keeper.txt`. Continuity is structural JSON, not generative. **Tonality presets** (`prompts/tonality/*.txt`) are the “prompt” for voice: bullet rules parsed into `ToneFingerprint` and injected as `{{tone_block}}` into writer, humanizer, combined/batch, and assembler—so tone cascades without re-asking the LLM what “Conversational” means each call.

## Associated prompt files
See dossier/14_tonality_presets.md — [prompts/tonality/](../prompts/tonality/)

## Implementation
`agents/memory_keeper.py` (no LLM invocation)
