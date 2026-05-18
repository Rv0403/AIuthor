# Researcher

## Purpose
Ground non-fiction (and fact-heavy) chapters by extracting cited facts and glossary candidates from RAG-retrieved corpus chunks only.

## Inputs
| Field | Source |
|-------|--------|
| `topic`, `chapter_title`, `chapter_summary`, `tone` | Outline + brief |
| `retrieved_context` | ChromaDB + optional BM25 (`rag/retriever.py`) |

Skipped when `skip_researcher_without_rag=true` and corpus is empty (facts list empty).

## Outputs
| Field | Type | Use |
|-------|------|-----|
| `ChapterResearch` | JSON | Writer, fact_checker, memory_keeper |
| `facts[]` | `{fact, source}` | Writer grounding; memory fact_registry |
| `references[]` | strings | Fact checker (generic only) |
| `glossary_candidates[]` | `{term, definition}` | Memory glossary |

## Known failure modes
| Failure | Mitigation |
|---------|------------|
| Empty retrieval | Prompt: return fewer facts, do not hallucinate |
| Fabricated studies/ISBNs | “Every fact MUST cite source”; fact_checker second pass |
| LLM ignores corpus | Retrieved context injected in full; abstain rules in prompt |
| Duplicate facts across chapters | memory_keeper dedupes by chapter commit |

## Why this prompt
- **Citation-or-abstain**: Separates generation from evidence; supports assessment “grounded non-fiction” requirement.
- **JSON facts**: Writer receives structured list, not raw chunks—reduces token noise and contradiction.
- **Glossary at research time**: Terms introduced when chapter is researched, not invented at assembly.
- **Tone in research**: Definitions can match Academic vs Conversational before writer sees them.

## Full prompt
See [prompts/researcher.txt](../prompts/researcher.txt)
