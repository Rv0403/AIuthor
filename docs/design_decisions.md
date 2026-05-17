# Design Decisions Log (Top 10)

1. **LangGraph over single prompt** — Assessment requires distinct agents with contracts; StateGraph gives conditional routing for Tests C/D without separate APIs.

2. **Single POST /execute** — Natural-language intent routing matches “orchestration engine” expectation; Intent Analyzer is always first node.

3. **Mixed model routing (Option C)** — Groq for all text agents (cheap/strong/reasoning/grounded); Gemini only for RAG embeddings. Avoids free-tier exhaustion on `gemini-2.0-flash` while keeping vector search. Researcher uses corpus RAG, not live Google Search, unless `GROUNDED_PROVIDER=gemini`.

4. **JSON memory store over context stuffing** — Fact registry, callbacks, glossary, and tone fingerprint persist per run; Writer receives only relevant slices.

5. **ChromaDB + optional BM25 hybrid** — Dense retrieval for semantic match; BM25 re-ranks when corpus is loaded in-memory for the run.

6. **Self-heal via structured renumbering** — Test D uses `repair.py` to shift chapter numbers and memory refs before generating inserted chapter; TOC rebuilt from outline metadata, never hardcoded in prose. Ambiguous insert position triggers chat/API clarification instead of defaulting `insert_after=4`.

7. **Tonality as ToneFingerprint** — Preset files in `prompts/tonality/` cascade to Assembler surfaces (preface, glossary, back cover), not only chapter bodies.

8. **Humanizer banned-phrase list in prompt dossier** — Explicit rejection gates; paired with `ai_tell_eval` regex checks.

9. **Preference-lite for openings** — Two-variant scoring via LLM judge documents path to full DPO/RLHF at scale without training infrastructure in 3 days.

10. **MOCK_LLM mode** — Enables CI and demo rehearsal without API keys; heuristics intent parser ensures Tests C/D routing still validates.

11. **Chat-style insert clarification** — Streamlit keeps conversation state (`messages`, `pending_insert`); same pattern as multi-turn chat UIs. API exposes `needs_clarification` for non-Streamlit clients.
