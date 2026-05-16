# Researcher Agent

## Purpose
Ground non-fiction chapters with RAG-retrieved facts and glossary candidates.

## Inputs
- chapter title/summary, topic, tone, retrieved_context

## Outputs
- `ChapterResearch` JSON with sourced facts

## Failure Modes
- Empty retrieval → fewer facts, no hallucination
- Fabricated references → blocked by prompt and Fact Checker

## Prompt Logic
Citation-or-abstain rule; sources must come from retrieved context only.

## Full Prompt
See [prompts/researcher.txt](../prompts/researcher.txt)
