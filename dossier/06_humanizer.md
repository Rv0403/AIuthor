# Humanizer Agent

## Purpose
Remove AI tells; add human voice, rhythm, and reader address.

## Inputs
- raw chapter text, tone_block, memory callbacks

## Outputs
- `humanized_text`

## Failure Modes
- Over-editing meaning → "preserve meaning" instruction
- Wrong person/tone → tone_block repeated

## Banned Phrases (MUST)
- delve into
- landscape of
- in today's fast-paced world / in today's world
- it's important to note / it is important to note
- furthermore / moreover (stacked)
- not only... but also (mechanical)
- leverage (buzzword)
- robust / seamless / cutting-edge (empty)

## Required
- Varied sentence lengths
- Emotional hooks
- Second-person where tone supports
- Domain metaphors
- Callback usage

## Full Prompt
See [prompts/humanizer.txt](../prompts/humanizer.txt)
