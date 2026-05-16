# Planner Agent

## Purpose
Create book title, chapter outline, summaries, and front/back matter plan.

## Inputs
- topic, reader, tone, genre, num_chapters, words_per_chapter, character_names

## Outputs
- `BookOutline` JSON

## Failure Modes
- Weak chapter progression → mitigated by requiring logical progression in prompt
- Tone drift in titles → tone repeated in prompt header

## Prompt Logic
Structured JSON-only output prevents regex parsing; chapter summaries seed Researcher queries.

## Full Prompt
See [prompts/planner.txt](../prompts/planner.txt)
