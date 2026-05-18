# AIuthor Workflow DAG

Directed acyclic graph for the LangGraph orchestrator (`graph/workflow.py`), chapter pipeline (`agents/chapter_pipeline.py`), and supporting stores.

For system layers, agents, and data flow, see **[architecture.md](architecture.md)**.

## Entry points

| Entry | File | Calls |
|-------|------|--------|
| Streamlit chat | `ui/streamlit_app.py` | `run_workflow()` |
| REST API | `api/main.py` → `POST /execute` | `run_workflow()` |
| CLI | `main.py` | `run_workflow()` |
| Scripts | `scripts/_common.py`, `scripts/run_test_d.py` | `run_workflow()` |

---

## 1. LangGraph orchestrator (top-level DAG)

Nodes are defined in `graph/workflow.py`; routing in `graph/routing.py`.

```mermaid
flowchart TD
    START([START]) --> intent[intent<br/>Intent Analyzer]

    intent -->|generate_book| init[init_generate]
    intent -->|tone_conversion<br/>insert_chapter<br/>export_book / repair_book<br/>regenerate_chapter| load[load_source<br/>Load snapshot]

    init --> planner[planner<br/>Planner + RAG ingest]

    load -->|needs_clarification| END1([END])
    load -->|tone_conversion| cp[chapter_pipeline]
    load -->|insert_chapter| prep[prepare_insert<br/>Memory repair / renumber]
    load -->|export_book / repair_book| asm[assembler]
    load -->|default| planner

    prep --> cp

    planner -->|current ≤ total| cp
    planner -->|current > total| asm

    cp -->|generate_book| adv[advance_chapter<br/>current_chapter += 1]
    cp -->|tone_conversion<br/>insert_chapter<br/>regenerate_chapter| asm

    adv -->|current ≤ total| cp
    adv -->|current > total| asm

    asm[assembler<br/>Manifest + PDF/DOCX] --> END2([END])
```

### Conditional edge reference

| From | Router | Outcomes |
|------|--------|----------|
| `intent` | `route_after_intent` | `generate_book` → `init_generate`; all other tasks → `load_source` |
| `load_source` | `route_after_load` | `needs_clarification` → END; `tone_conversion` → `chapter_pipeline`; `insert_chapter` → `prepare_insert`; `export_book` / `repair_book` → `assembler`; else → `planner` |
| `planner` | `should_continue_chapters` | `chapter_loop` → `chapter_pipeline`; else → `assembler` |
| `chapter_pipeline` | `route_after_chapter_pipeline` | single-chapter tasks → `assembler`; `generate_book` → `advance_chapter` |
| `advance_chapter` | `should_continue_chapters` | loop → `chapter_pipeline`; else → `assembler` |

### Task-type paths

```mermaid
flowchart LR
    subgraph generate_book
        I1[intent] --> G1[init_generate] --> P1[planner] --> L1[chapter loop] --> A1[assembler]
    end

    subgraph tone_conversion
        I2[intent] --> L2[load_source] --> C2[chapter_pipeline] --> A2[assembler]
    end

    subgraph insert_chapter
        I3[intent] --> L3[load_source] --> V{valid insert_after?}
        V -->|no| CL[END: needs_clarification]
        V -->|yes| R3[prepare_insert] --> C3[chapter_pipeline] --> A3[assembler]
    end
```

---

## 2. Chapter pipeline sub-DAG

Invoked inside the `chapter_pipeline` node. Mode is chosen by `choose_chapter_pipeline_mode()` in `utils/context_budget.py` (`batch` | `combined` | `split`, or `chapter_pipeline_mode` on state).

```mermaid
flowchart TD
    subgraph mode_select["Mode selection (auto)"]
        M{batch / combined / split}
    end

    CP_IN([chapter_pipeline in]) --> M

    M -->|batch| B_PATH
    M -->|combined| C_PATH
    M -->|split| S_PATH

    subgraph B_PATH["batch — one LLM for all chapters"]
        BR[memory_read] --> BB[chapters_batch]
        BB --> BW["memory_write × N"]
    end

    subgraph C_PATH["combined — one LLM per chapter (default)"]
        CR[memory_read] --> CC[chapter_combined]
        CC --> CW[memory_write]
    end

    subgraph S_PATH["split — one LLM per agent (large chapters)"]
        SR[memory_read] --> R[researcher]
        R --> W[writer]
        W --> H[humanizer]
        H --> E[editor]
        E --> F[fact_checker]
        F --> SW[memory_write]
    end

    B_PATH --> CP_OUT([chapter_pipeline out])
    C_PATH --> CP_OUT
    S_PATH --> CP_OUT
```

| Mode | When | LLM agents | Memory |
|------|------|------------|--------|
| `batch` | Few short chapters fit one prompt | `chapters_batch` | read once, write per chapter |
| `combined` | Default per-chapter budget | `chapter_combined` | read + write per chapter |
| `split` | Chapter exceeds token budget | researcher → writer → humanizer → editor → fact_checker | read + write per chapter |

`memory_read` / `memory_write` are deterministic (no LLM) in `agents/memory_keeper.py`.

---

## 3. Data & side-effect edges

Agents read/write shared `BookState` and external stores (not separate graph nodes).

```mermaid
flowchart TB
    subgraph agents["LLM agents"]
        IA[intent_analyzer]
        PL[planner]
        RS[researcher / chapter_combined / chapters_batch]
        WR[writer]
        HU[humanizer]
        ED[editor]
        FC[fact_checker]
        AS[assembler]
    end

    subgraph state["BookState (LangGraph)"]
        ST[outline · chapters · memory · brief · current_chapter]
    end

    subgraph stores["Persistent stores"]
        CH[(ChromaDB .chroma/)]
        MJ[(outputs/run_id/memory.json)]
        SN[(outputs/run_id/snapshot.json)]
        TR[(traces/run_id/*.jsonl)]
        OUT[(outputs/run_id/*.pdf .docx manifest.json)]
    end

    IA --> ST
    PL --> ST
    PL -->|ingest_corpus| CH
    RS -->|RAGRetriever| CH
    RS --> ST
    WR --> ST
    HU --> ST
    ED --> ST
    FC --> ST
    AS --> ST
    AS --> OUT
    ST --> MJ
    ST --> SN
    agents --> TR
```

---

## 4. Agent inventory

| Graph node | Agent module | Role |
|------------|--------------|------|
| `intent` | `agents/intent_analyzer.py` | Parse NL brief → `task_type`, `brief`, routing |
| `load_source` | `memory/memory_store.py` | Load prior run snapshot |
| `prepare_insert` | `memory/repair.py` | Renumber outline/chapters after insert |
| `init_generate` | `graph/nodes.py` | Reset chapter counters for new book |
| `planner` | `agents/planner.py` | `BookOutline` + corpus ingest |
| `chapter_pipeline` | `agents/chapter_pipeline.py` | Adaptive chapter generation |
| `advance_chapter` | `graph/nodes.py` | Increment `current_chapter` |
| `assembler` | `agents/assembler.py` | `BookManifest` + export |

Supporting (non-graph): `agents/insert_clarification.py` (insert validation), `agents/intent_heuristics.py`, `evals/*` (post-run via API when `auto_run_evals`).

---

## 5. State keys that drive routing

| Key | Set by | Used for |
|-----|--------|----------|
| `task_type` | intent | `route_after_intent`, `route_after_load`, `route_after_chapter_pipeline` |
| `status` | load_source (insert invalid) | `needs_clarification` → END |
| `current_chapter` | planner, advance_chapter, batch pipeline | `should_continue_chapters` |
| `total_chapters` | planner, prepare_insert, load_source | chapter loop termination |
| `insert_after` | intent / user / clarification resume | insert path |
| `source_run_id` | intent / load | snapshot source |

Source of truth for graph construction: `graph/workflow.py`, `graph/routing.py`, `graph/nodes.py`, `graph/state.py`.
