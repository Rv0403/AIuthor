# Planner

## Purpose
Produce a publication-ready book outline—title, chapter list with summaries, and front/back matter plan—that seeds the chapter loop and assembler.

## Inputs
| Field | Source |
|-------|--------|
| `topic`, `reader`, `tone`, `genre` | Intent + brief |
| `num_chapters`, `words_per_chapter` | Intent |
| `character_names` | Intent (fiction) |

## Outputs
| Field | Type | Use |
|-------|------|-----|
| `BookOutline` | JSON | Chapter loop, TOC, assembler |
| `title`, `subtitle`, `chapters[]` | | Per-chapter `title`, `summary`, `target_words` |
| `front_matter_plan`, `back_matter_plan` | lists | Assembler surface checklist |

## Known failure modes
| Failure | Mitigation |
|---------|------------|
| Weak chapter progression | Prompt requires logical progression and cross-chapter callbacks in summaries |
| Tone drift in titles | Tone repeated in prompt header; summaries must match tonality |
| Invalid JSON | `invoke_structured` + schema validation |
| Over-long outline for context | Planner runs once; summaries kept to 2–3 sentences |

## Why this prompt
- **Structured outline only**: JSON prevents regex scraping; downstream agents consume stable fields.
- **Assessment alignment**: `num_chapters` and `words_per_chapter` come from intent so Tests A/B hit requested scale.
- **Front/back matter plan**: Ensures assembler generates full book surfaces, not chapters-only PDFs.
- **Callback planning**: “Callbacks planned across chapters” in prompt seeds memory_keeper and writer continuity.

## Full prompt
See [prompts/planner.txt](../prompts/planner.txt)
