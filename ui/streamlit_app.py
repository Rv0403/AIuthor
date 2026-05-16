"""Streamlit demo UI for AIuthor."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from config import get_settings
from evals.run_evals import run_all_evals
from graph.workflow import run_workflow
from memory.memory_store import MemoryStore

st.set_page_config(page_title="AIuthor", page_icon="📚", layout="wide")
st.title("AIuthor — Agentic Book Generation")

settings = get_settings()

EXAMPLE_INPUTS = [
    "A 10-chapter beginner's guide to personal finance, Conversational tone, approximately 2500 words per chapter",
    "A 5-chapter novella, Storyteller tone, two named characters Arjun and Maya carried throughout",
    "Using run <run_id>, regenerate Chapter 3 in Academic tone",
    "Using run <run_id>, regenerate Chapter 3 in Motivational tone",
    "Using run <run_id>, regenerate Chapter 3 in Witty tone",
    "Insert a new chapter between Chapter 4 and 5 in book run <run_id>",
]

col1, col2 = st.columns([2, 1])

with col1:
    user_input = st.text_area(
        "Natural language task",
        height=120,
        placeholder="Enter your task, or copy an example below",
    )
    st.markdown("**Examples**")
    for i, example in enumerate(EXAMPLE_INPUTS, start=1):
        st.markdown(f"{i}. {example}")

with col2:
    mock = st.checkbox("Mock LLM (offline)", value=settings.mock_llm)
    if mock:
        import os
        os.environ["MOCK_LLM"] = "true"

if st.button("Execute", type="primary"):
    with st.spinner("Running agent pipeline…"):
        try:
            result = run_workflow(user_input)
            st.session_state["last_result"] = result
        except Exception as e:
            st.error(str(e))

if "last_result" in st.session_state:
    r = st.session_state["last_result"]
    st.success(f"Run `{r.get('run_id')}` — {r.get('status', 'done')}")
    st.json({k: v for k, v in r.items() if k not in ("chapters", "memory", "manifest")})

    paths = r.get("output_paths", {})
    for label, path in paths.items():
        p = Path(path)
        if p.exists():
            with open(p, "rb") as f:
                st.download_button(f"Download {label.upper()}", f, file_name=p.name)

    run_id = r.get("run_id")
    if run_id:
        if st.button("Run evals"):
            report = run_all_evals(run_id)
            st.json(report)

        trace_dir = settings.traces_dir / run_id
        if trace_dir.exists():
            st.subheader("Trace files")
            for f in trace_dir.glob("*.jsonl"):
                st.text(f.name)
                st.code(f.read_text(encoding="utf-8")[:3000])

st.sidebar.header("Recent runs")
for rid in MemoryStore.list_runs()[:10]:
    st.sidebar.write(rid)
