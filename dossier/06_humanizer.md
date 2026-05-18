# Humanizer

## Purpose
Rewrite draft prose to sound human: remove AI tells, vary rhythm, address the reader per tone, and weave memory callbacks.

## Inputs
| Field | Source |
|-------|--------|
| `chapter_text` | Writer `raw_text` (split mode) |
| `tone_block` | Memory / override |
| `memory_context` | Callbacks and facts |

## Outputs
| Field | Use |
|-------|-----|
| `humanized_text` | Editor input |

## Known failure modes
| Failure | Mitigation |
|---------|------------|
| Meaning drift | “Preserve meaning and factual content” |
| Wrong register (too casual/academic) | `tone_block` + REQUIRED humanization per tone |
| Banned phrases survive | Explicit MUST-remove list; paired with `ai_tell_eval` regex |
| Over-long output | Full chapter rewrite instructed |

## Known banned phrases (prompt-enforced)
- delve into · landscape of · in today's fast-paced world / in today's world
- it is important to note / it's important to note
- furthermore / moreover (stacked) · not only... but also (mechanical)
- leverage (buzzword) · robust / seamless / cutting-edge (empty modifiers)

## Why this prompt
- **Dedicated anti-AI-tell agent**: Assessment scores human voice; separating humanization from writing avoids one prompt doing everything poorly.
- **Explicit ban list**: Models regress on “avoid AI language”; named phrases are auditable in dossier and evals.
- **Tone-specific behavior**: Second-person and metaphor rules differ for Conversational vs Academic in one place.
- **Callback pass**: Forces continuity at voice layer, not only fact layer.

## Full prompt
See [prompts/humanizer.txt](../prompts/humanizer.txt)
