# Writer Agent

## Purpose
Generate chapter draft from outline, memory, research, and tone fingerprint.

## Inputs
- chapter outline, memory context, facts, tone_block, target_words

## Outputs
- `raw_text` prose

## Failure Modes
- Repetitive openings → Humanizer and preference-lite loop
- Ungrounded facts → prompt forbids for non-fiction

## Prompt Logic
Tone block injected from ToneFingerprint; callbacks listed explicitly.

## Full Prompt
See [prompts/writer.txt](../prompts/writer.txt)
