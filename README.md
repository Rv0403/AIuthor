# AIuthor — Agentic Book Generation System

Gateway Digital AI Engineer Assessment: multi-agent LangGraph pipeline that produces publication-ready books with memory, tonality, RAG grounding, observability, and self-healing chapter insertion.

## Quick start

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Add OPENAI_API_KEY and/or ANTHROPIC_API_KEY to .env
```

### One-command test runs

```bash
python -m scripts.run_test_a
python -m scripts.run_test_b
python -m scripts.run_test_c
python -m scripts.run_test_d
```

### API + Streamlit demo

```bash
uvicorn api.main:app --reload --port 8000
streamlit run ui/streamlit_app.py
```

POST to `http://localhost:8000/execute` with:

```json
{"user_input": "A 10 chapter beginner guide to personal finance in conversational tone"}
```

## Architecture

- **Orchestration:** LangGraph with Intent Analyzer → conditional workflows
- **Agents:** Planner, Researcher, Memory Keeper, Writer, Humanizer, Editor, Fact Checker, Assembler
- **Memory:** Fact registry, character bible, callback index, tone fingerprint, decision log
- **Outputs:** PDF + DOCX per run in `outputs/{run_id}/`
- **Traces:** `traces/{run_id}/` — prompt log, agent trace, memory I/O, token ledger

## Documentation

- [docs/architecture.md](docs/architecture.md)
- [docs/memory_schema.md](docs/memory_schema.md)
- [docs/design_decisions.md](docs/design_decisions.md)
- [docs/evals_report.md](docs/evals_report.md)
- Prompt dossier: `dossier/` → `python -m dossier.build_dossier_pdf`

## Test cases (assessment)

| Test | Command | Description |
|------|---------|-------------|
| A | `run_test_a` | 10-chapter personal finance, Conversational |
| B | `run_test_b` | 5-chapter novella, Storyteller |
| C | `run_test_c` | Regenerate ch3 in Academic, Motivational, Witty |
| D | `run_test_d` | Insert chapter after ch4 — self-heal TOC/callbacks/glossary |
