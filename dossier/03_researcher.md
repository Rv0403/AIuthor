# Researcher Agent

## Purpose
Ground non-fiction chapters with RAG-retrieved facts and glossary candidates from the run corpus (ChromaDB).

## Model routing (default)
Groq `llama-3.3-70b-versatile` via `GROUNDED_PROVIDER=groq` (Option C). Local RAG context is injected into the prompt; live Google Search grounding is only used when `GROUNDED_PROVIDER=gemini`.

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
