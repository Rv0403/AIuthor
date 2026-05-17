# AIuthor Architecture

## Topology

```mermaid
flowchart TB
    UI[Streamlit chat] --> API[POST /execute]
    API --> Intent[Intent Analyzer]
    Intent --> Router{task_type}
    Router -->|generate_book| Planner --> ChapterLoop
    Router -->|tone_conversion| LoadSource --> ChapterLoop
    Router -->|insert_chapter| LoadSource --> Valid{insert_after valid?}
    Valid -->|no| Clarify[needs_clarification → chat prompt]
    Clarify --> UI
    Valid -->|yes| Repair[prepare_insert / repair] --> ChapterLoop
  ChapterLoop[Research → Memory → Write → Humanize → Edit → FactCheck → Memory]
    ChapterLoop --> Assembler
    Assembler --> Export[PDF + DOCX]
    ChapterLoop --> Traces[(traces/run_id)]
    Research --> Chroma[(ChromaDB)]
    Memory --> JSON[(outputs/run_id/memory.json)]
```

## Orchestration pattern

**LangGraph StateGraph** with conditional edges on `task_type`. Single natural-language entry point; no per-task REST routes.

| Workflow | Trigger | Path |
|----------|---------|------|
| `generate_book` | New book brief | Intent → Planner → chapter loop → Assembler |
| `tone_conversion` | Regenerate chapter in new tone | Intent → Load snapshot → single chapter loop → Assembler |
| `insert_chapter` | Insert between N and N+1 | Intent → Load → validate position → (clarify if needed) → Repair renumber → generate new chapter → Assembler |

## Memory stores

| Store | Location | Contents |
|-------|----------|----------|
| Structured memory | `outputs/{run_id}/memory.json` | Facts, callbacks, glossary, characters, tone fingerprint, decision log |
| Snapshot | `outputs/{run_id}/snapshot.json` | Full run state for Tests C/D |
| Vector RAG | `.chroma/` | Chunked corpus embeddings per collection |
| Traces | `traces/{run_id}/*.jsonl` | Prompts, agent trace, memory I/O, token ledger |

## Data flow

1. User brief → Intent Analyzer (structured JSON).
2. Planner produces `BookOutline`.
3. Per chapter: RAG retrieval → Researcher facts → Memory read → Writer → Humanizer → Editor → Fact Checker → Memory write.
4. Assembler builds manifest (front/back matter in tone) → DOCX/PDF export.

## Failure paths

- Missing API keys: set `MOCK_LLM=true` for structural validation.
- RAG empty: Researcher returns fewer facts; Writer instructed not to invent.
- Fact Checker: softens unverifiable claims; never fabricates ISBNs.
- Insert repair: `memory/repair.py` renumbers chapters and shifts callback/glossary refs before regeneration.
- Ambiguous insert position: workflow returns `needs_clarification`; Streamlit chat asks for a valid chapter (no default `insert_after=4`).

## Model routing

- **Strong** (Writer, Humanizer, Editor, Assembler): Groq `llama-3.3-70b-versatile`.
- **Reasoning** (Planner): Groq `llama-3.3-70b-versatile`.
- **Grounded** (Researcher; RAG corpus only, no live Google Search): Groq `llama-3.1-8b-instant`.
- **Cheap** (Intent, Fact Checker, eval judges): Groq `llama-3.1-8b-instant`.
- **Embeddings** (RAG): Gemini `gemini-embedding-001`.
