# Design Decisions Log (Top 10)

1. **LangGraph over single prompt** — Assessment requires distinct agents with contracts; StateGraph gives conditional routing for Tests C/D without separate APIs.

2. **Single POST /execute** — Natural-language intent routing matches “orchestration engine” expectation; Intent Analyzer is always first node.

3. **Mixed model routing** — Strong models for prose generation; cheap models for intent, research structuring, fact-check, and eval judges to control cost (~10x savings on non-creative steps).

4. **JSON memory store over context stuffing** — Fact registry, callbacks, glossary, and tone fingerprint persist per run; Writer receives only relevant slices.

5. **ChromaDB + optional BM25 hybrid** — Dense retrieval for semantic match; BM25 re-ranks when corpus is loaded in-memory for the run.

6. **Self-heal via structured renumbering** — Test D uses `repair.py` to shift chapter numbers and memory refs before generating inserted chapter; TOC rebuilt from outline metadata, never hardcoded in prose.

7. **Tonality as ToneFingerprint** — Preset files in `prompts/tonality/` cascade to Assembler surfaces (preface, glossary, back cover), not only chapter bodies.

8. **Humanizer banned-phrase list in prompt dossier** — Explicit rejection gates; paired with `ai_tell_eval` regex checks.

9. **Preference-lite for openings** — Two-variant scoring via LLM judge documents path to full DPO/RLHF at scale without training infrastructure in 3 days.

10. **MOCK_LLM mode** — Enables CI and demo rehearsal without API keys; heuristics intent parser ensures Tests C/D routing still validates.
