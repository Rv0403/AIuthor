# Memory Keeper Agent

## Purpose
Maintain cross-chapter continuity via fact registry, callbacks, glossary, characters, tone fingerprint, decision log.

## Inputs
- Current chapter number, research output, verified chapter text

## Outputs
- Updated `BookMemory` persisted to disk

## Failure Modes
- Callback spam → only first 120 chars of chapter stored as callback seed
- Test D breakage → repair.py shifts refs before write (only after valid `insert_after`; see dossier/10_insert_clarification.md)

## Prompt Logic
Read before Writer (relevant slices); write after Fact Checker (commit facts/callbacks).

## Full Prompt
N/A — deterministic merge logic in `agents/memory_keeper.py`
