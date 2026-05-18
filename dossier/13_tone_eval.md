# Tone Eval (evaluation judge)

## Purpose
Score how well a text sample matches the requested tone (1–5). Used by `evals/tone_eval.py` and optional **preference-lite** opening selection (`pick_best_opening`).

## Inputs
| Field | Source |
|-------|--------|
| `tone` | Brief / Test C override (Conversational, Academic, etc.) |
| `text_sample` | First ~4000 chars of chapter or opening variant |

## Outputs
| Field | Use |
|-------|-----|
| Numeric score 1–5 + one-sentence justification | Normalized to 0–1; `passed` if ≥ 0.6 |
| Eval report | `evals/run_evals.py` when `auto_run_evals=true` |

Not part of the LangGraph book pipeline; runs post-hoc or inside humanizer variant loop.

## Known failure modes
| Failure | Mitigation |
|---------|------------|
| Non-numeric LLM reply | Regex extract first number; default 0.7 on parse failure |
| Judge too lenient | Paired with `ai_tell_eval` banned-phrase checks |
| Short sample | Empty text → score 0, failed |

## Why this prompt
- **Measurable tonality**: Assessment asks for tone fidelity; a dedicated judge is reproducible in eval reports.
- **Minimal output**: Single number + sentence keeps judge calls cheap (`tier=cheap`).
- **Preference-lite path**: Documents route to full DPO/RLHF without training infra—compare opening variants by score.
- **Test C support**: Validates regenerate-in-new-tone actually shifted voice.

## Full prompt
See [prompts/eval_tone.txt](../prompts/eval_tone.txt)
