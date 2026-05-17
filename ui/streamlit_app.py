"""Streamlit demo UI for AIuthor — chat-style task input with insert clarification."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from agents.insert_clarification import invalid_reply_prompt, parse_insert_after
from config import get_settings
from evals.run_evals import run_all_evals
from graph.workflow import run_workflow
from memory.memory_store import MemoryStore

st.set_page_config(page_title="AIuthor", page_icon="📚", layout="wide")
st.title("AIuthor — Agentic Book Generation")

settings = get_settings()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_insert" not in st.session_state:
    st.session_state.pending_insert = None
if "last_result" not in st.session_state:
    st.session_state.last_result = None

EXAMPLE_INPUTS = [
    "A 10-chapter beginner's guide to personal finance, Conversational tone, approximately 2500 words per chapter",
    "A 5-chapter novella, Storyteller tone, two named characters Arjun and Maya carried throughout",
    "Using run <run_id>, regenerate Chapter 3 in Academic tone",
    "Using run <run_id>, regenerate Chapter 3 in Motivational tone",
    "Using run <run_id>, regenerate Chapter 3 in Witty tone",
    "Insert a new chapter between Chapter 4 and 5 in book run <run_id>",
]

col1, col2 = st.columns([2, 1])

with col2:
    mock = st.checkbox("Mock LLM (offline)", value=settings.mock_llm)
    if mock:
        import os

        os.environ["MOCK_LLM"] = "true"
    if st.button("Clear chat"):
        st.session_state.messages = []
        st.session_state.pending_insert = None
        st.session_state.last_result = None
        st.rerun()

with col1:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    def _run_pipeline(user_text: str, pending: dict | None) -> None:
        st.session_state.messages.append({"role": "user", "content": user_text})

        if pending:
            total = pending["total_chapters"]
            insert_after = parse_insert_after(user_text)
            if insert_after is None:
                reply = invalid_reply_prompt(total)
                st.session_state.messages.append({"role": "assistant", "content": reply})
                return

            from agents.insert_clarification import validate_insert_after

            ok, reason = validate_insert_after(insert_after, total)
            if not ok:
                st.session_state.messages.append(
                    {"role": "assistant", "content": reason if reason != "missing" else invalid_reply_prompt(total)}
                )
                return

            with st.spinner("Inserting chapter…"):
                try:
                    result = run_workflow(
                        pending["user_input"],
                        run_id=pending.get("run_id"),
                        task_type="insert_chapter",
                        insert_after=insert_after,
                        source_run_id=pending["source_run_id"],
                        intent={**pending.get("intent", {}), "insert_after": insert_after},
                        brief=pending.get("brief"),
                    )
                    st.session_state.pending_insert = None
                    st.session_state.last_result = result
                    if result.get("status") == "needs_clarification":
                        st.session_state.pending_insert = result.get("pending_insert")
                        st.session_state.messages.append(
                            {"role": "assistant", "content": result.get("clarification_message", "Need more detail.")}
                        )
                    else:
                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "content": f"Done — run `{result.get('run_id')}` ({result.get('status', 'completed')}).",
                            }
                        )
                except Exception as e:
                    st.session_state.messages.append({"role": "assistant", "content": f"Error: {e}"})
            return

        with st.spinner("Running agent pipeline…"):
            try:
                result = run_workflow(user_text)
                st.session_state.last_result = result
                if result.get("status") == "needs_clarification":
                    pending = dict(result.get("pending_insert") or {})
                    pending.setdefault("user_input", user_text)
                    pending["run_id"] = result.get("run_id")
                    st.session_state.pending_insert = pending
                    st.session_state.messages.append(
                        {"role": "assistant", "content": result.get("clarification_message", "Please specify the chapter.")}
                    )
                else:
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": f"Run `{result.get('run_id')}` — {result.get('status', 'done')}.",
                        }
                    )
            except Exception as e:
                st.session_state.messages.append({"role": "assistant", "content": f"Error: {e}"})

    prompt = st.chat_input(
        "Describe your task, or reply with a chapter number…"
        if st.session_state.pending_insert
        else "Describe your task…"
    )
    if prompt:
        _run_pipeline(prompt, st.session_state.pending_insert)
        st.rerun()

st.markdown("**Examples** (click to use)")
for i, example in enumerate(EXAMPLE_INPUTS, start=1):
    if st.button(f"{i}. {example[:70]}…" if len(example) > 70 else f"{i}. {example}", key=f"ex_{i}"):
        _run_pipeline(example, None)
        st.rerun()

if st.session_state.last_result:
    r = st.session_state.last_result
    if r.get("status") not in ("needs_clarification",):
        with st.expander("Last run details", expanded=False):
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
