# Tonality Presets (shared prompt fragments)

## Purpose
Define **tone rules** loaded by Memory Keeper into `ToneFingerprint`, then injected as `{{tone_block}}` into Writer, Humanizer, Chapter Combined, Chapters Batch, and Assembler. Not standalone LLM calls—fragments concatenated into agent prompts.

## Inputs
| Field | Source |
|-------|--------|
| `tone` name from intent | `Conversational`, `Academic`, `Storyteller`, `Motivational`, `Witty` |
| File path | `prompts/tonality/{tone.lower()}.txt` |

## Outputs
| Field | Use |
|-------|-----|
| `ToneFingerprint { tone, rules[] }` | `format_tone_block()` in agent prompts |

## Presets (one file per assessment tone)

### Conversational
- **File**: [prompts/tonality/conversational.txt](../prompts/tonality/conversational.txt)
- **Why**: Test A default; second-person, simple language, friendly glossary.
- **Failure modes**: Drift to academic jargon → rules forbid formal structure.

### Academic
- **File**: [prompts/tonality/academic.txt](../prompts/tonality/academic.txt)
- **Why**: Test C regenerate target; third-person, evidence framing, scholarly glossary.
- **Failure modes**: Dry lists → writer/humanizer still require hooks where prompt allows.

### Storyteller
- **File**: [prompts/tonality/storyteller.txt](../prompts/tonality/storyteller.txt)
- **Why**: Test B novella; scene, pacing, in-world glossary.
- **Failure modes**: Over-exposition → show-through-action rules.

### Motivational
- **File**: [prompts/tonality/motivational.txt](../prompts/tonality/motivational.txt)
- **Why**: Test C option; direct address, action steps, energizing back cover.
- **Failure modes**: Empty hype → “anchor encouragement in specifics”.

### Witty
- **File**: [prompts/tonality/witty.txt](../prompts/tonality/witty.txt)
- **Why**: Test C option; humor without undermining trust.
- **Failure modes**: Sarcasm eroding credibility → explicit avoid rule.

## Known failure modes (all presets)
| Failure | Mitigation |
|---------|------------|
| Missing file for tone name | Fallback: single generic rule in `memory_keeper._load_tone_preset` |
| Tone only in chapters, not matter | Assembler prompt requires cascade to all surfaces |
| Override not applied | Test C sets `tone_override` on state before chapter pipeline |

## Why separate preset files (not inline in writer.txt)
- **Single source of truth**: Change Conversational once; all agents inherit via `tone_block`.
- **Assessment tones map 1:1** to files for eval and documentation.
- **Assembler + chapter agents stay DRY**: Same fingerprint for body and back matter.
- **Eval alignment**: `eval_tone.txt` judges against the same tone label the preset defines.

## Full prompt files
| Tone | Path |
|------|------|
| Conversational | [prompts/tonality/conversational.txt](../prompts/tonality/conversational.txt) |
| Academic | [prompts/tonality/academic.txt](../prompts/tonality/academic.txt) |
| Storyteller | [prompts/tonality/storyteller.txt](../prompts/tonality/storyteller.txt) |
| Motivational | [prompts/tonality/motivational.txt](../prompts/tonality/motivational.txt) |
| Witty | [prompts/tonality/witty.txt](../prompts/tonality/witty.txt) |
