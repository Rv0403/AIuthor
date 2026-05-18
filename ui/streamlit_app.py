"""Streamlit demo UI for AIuthor — chat-style task input with insert clarification."""
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from agents.insert_clarification import invalid_reply_prompt, parse_insert_after, validate_insert_after
from config import get_settings
from evals.run_evals import run_all_evals
from graph.workflow import run_workflow
from memory.memory_store import MemoryStore
from ui.chat_store import (
    ensure_active_session,
    list_sessions,
    load_session,
    migrate_legacy_chat_if_needed,
    new_session,
    save_session,
)

st.set_page_config(page_title="AIuthor", page_icon="📚", layout="wide")
st.title("AIuthor — Agentic Book Generation")

settings = get_settings()


def _apply_session(session_id: str) -> None:
    data = load_session(session_id)
    st.session_state.session_id = session_id
    st.session_state.messages = data["messages"]
    st.session_state.pending_insert = data["pending_insert"]
    st.session_state.last_result = data.get("last_result")
    st.session_state.chat_hydrated = True


def _start_new_chat() -> None:
    sid = new_session()
    st.session_state.session_id = sid
    st.session_state.messages = []
    st.session_state.pending_insert = None
    st.session_state.pending_run = None
    st.session_state.last_result = None
    save_session(sid, [], pending_insert=None, last_result=None)


if "chat_hydrated" not in st.session_state:
    migrated = migrate_legacy_chat_if_needed()
    sid = migrated or ensure_active_session()
    _apply_session(sid)

if "session_id" not in st.session_state:
    st.session_state.session_id = ensure_active_session()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_insert" not in st.session_state:
    st.session_state.pending_insert = None
if "pending_run" not in st.session_state:
    st.session_state.pending_run = None
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


def _persist_chat() -> None:
    save_session(
        st.session_state.session_id,
        st.session_state.messages,
        pending_insert=st.session_state.pending_insert,
        last_result=st.session_state.last_result,
    )


def _append_message(role: str, content: str) -> None:
    st.session_state.messages.append({"role": role, "content": content})
    _persist_chat()


def _new_run_id() -> str:
    return str(uuid.uuid4())[:12]


def _execute_run(user_text: str, pending: dict | None) -> None:
    """Run pipeline and append assistant reply (user message already in chat history)."""
    if pending:
        total = pending["total_chapters"]
        insert_after = parse_insert_after(user_text)
        if insert_after is None:
            _append_message("assistant", invalid_reply_prompt(total))
            return

        ok, reason = validate_insert_after(insert_after, total)
        if not ok:
            _append_message(
                "assistant",
                reason if reason != "missing" else invalid_reply_prompt(total),
            )
            return

        run_id = pending.get("run_id") or _new_run_id()
        with st.spinner(f"Inserting chapter (run `{run_id}`)…"):
            try:
                result = run_workflow(
                    pending["user_input"],
                    run_id=run_id,
                    task_type="insert_chapter",
                    insert_after=insert_after,
                    source_run_id=pending["source_run_id"],
                    intent={**pending.get("intent", {}), "insert_after": insert_after},
                    brief=pending.get("brief"),
                )
                st.session_state.pending_insert = None
                st.session_state.last_result = result
                if result.get("status") == "needs_clarification":
                    pending_state = dict(result.get("pending_insert") or {})
                    pending_state.setdefault("user_input", pending["user_input"])
                    pending_state["run_id"] = result.get("run_id")
                    st.session_state.pending_insert = pending_state
                    _append_message(
                        "assistant",
                        result.get("clarification_message", "Need more detail."),
                    )
                else:
                    _append_message(
                        "assistant",
                        f"Done — run `{result.get('run_id')}` ({result.get('status', 'completed')}). "
                        f"Traces: `traces/{result.get('run_id')}/`",
                    )
            except Exception as e:
                _append_message("assistant", f"Error: {e}")
        return

    run_id = _new_run_id()
    with st.spinner(f"Running pipeline (run `{run_id}`)…"):
        try:
            result = run_workflow(user_text, run_id=run_id)
            st.session_state.last_result = result
            if result.get("status") == "needs_clarification":
                pending_state = dict(result.get("pending_insert") or {})
                pending_state.setdefault("user_input", user_text)
                pending_state["run_id"] = result.get("run_id", run_id)
                st.session_state.pending_insert = pending_state
                _append_message(
                    "assistant",
                    result.get("clarification_message", "Please specify the chapter."),
                )
            else:
                _append_message(
                    "assistant",
                    f"Run `{result.get('run_id')}` — {result.get('status', 'done')}. "
                    f"Traces: `traces/{result.get('run_id')}/`",
                )
        except Exception as e:
            _append_message(
                "assistant",
                f"Error (run `{run_id}`): {e}\n\n"
                "Use **New chat** in the sidebar to start a fresh thread with a new trace folder.",
            )


# —— Sidebar: sessions ——
st.sidebar.header("Chat")
if st.sidebar.button("New chat", type="primary", use_container_width=True):
    _start_new_chat()
    st.rerun()

st.sidebar.caption("Each new chat gets its own `run_id` and trace folder under `traces/`.")

sessions = list_sessions()
if sessions:
    st.sidebar.subheader("Previous chats")
    for sess in sessions[:12]:
        sid = sess["session_id"]
        label = sess.get("title") or sid
        count = sess.get("message_count", 0)
        is_active = sid == st.session_state.session_id
        if st.sidebar.button(
            f"{'• ' if is_active else ''}{label} ({count})",
            key=f"switch_{sid}",
            use_container_width=True,
        ):
            if sid != st.session_state.session_id:
                _apply_session(sid)
                st.session_state.pending_run = None
                st.rerun()

st.sidebar.divider()
st.sidebar.header("Recent runs")
for rid in MemoryStore.list_runs()[:10]:
    st.sidebar.write(f"`{rid}`")

# —— Main ——
col1, col2 = st.columns([2, 1])

with col2:
    mock = st.checkbox("Mock LLM (offline)", value=settings.mock_llm)
    if mock:
        import os

        os.environ["MOCK_LLM"] = "true"
    st.caption(f"Session `{st.session_state.session_id}`")

with col1:
    with st.expander("Example prompts (copy into chat)", expanded=False):
        for i, example in enumerate(EXAMPLE_INPUTS, start=1):
            st.markdown(f"**{i}.** {example}")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if st.session_state.pending_run:
        job = st.session_state.pending_run
        st.session_state.pending_run = None
        _execute_run(job["text"], job.get("pending"))
        st.rerun()

    prompt = st.chat_input(
        "Describe your task, or reply with a chapter number…"
        if st.session_state.pending_insert
        else "Describe your task…"
    )
    if prompt and not st.session_state.pending_run:
        _append_message("user", prompt)
        st.session_state.pending_run = {
            "text": prompt,
            "pending": st.session_state.pending_insert,
        }
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
