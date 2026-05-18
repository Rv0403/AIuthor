"""Persist Streamlit chat sessions to disk (multiple threads)."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import get_settings


def _chat_root() -> Path:
    path = get_settings().outputs_dir / ".ui_chat"
    path.mkdir(parents=True, exist_ok=True)
    return path


def sessions_dir() -> Path:
    path = _chat_root() / "sessions"
    path.mkdir(parents=True, exist_ok=True)
    return path


def active_session_path() -> Path:
    return _chat_root() / "active_session.txt"


def _session_path(session_id: str) -> Path:
    return sessions_dir() / f"{session_id}.json"


def create_session_id() -> str:
    return str(uuid.uuid4())[:10]


def get_active_session_id() -> str | None:
    path = active_session_path()
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def set_active_session_id(session_id: str) -> None:
    active_session_path().write_text(session_id, encoding="utf-8")


def load_session(session_id: str) -> dict[str, Any]:
    path = _session_path(session_id)
    if not path.exists():
        return _empty_session(session_id)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return _empty_session(session_id)
    return {
        "session_id": session_id,
        "title": data.get("title") or "New chat",
        "created_at": data.get("created_at", ""),
        "messages": data.get("messages") or [],
        "pending_insert": data.get("pending_insert"),
        "last_result": data.get("last_result"),
    }


def _empty_session(session_id: str) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "title": "New chat",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "messages": [],
        "pending_insert": None,
        "last_result": None,
    }


def _session_title(messages: list[dict[str, str]]) -> str:
    for msg in messages:
        if msg.get("role") == "user":
            text = (msg.get("content") or "").strip().replace("\n", " ")
            return text[:48] + ("…" if len(text) > 48 else "")
    return "New chat"


def save_session(
    session_id: str,
    messages: list[dict[str, str]],
    *,
    pending_insert: dict[str, Any] | None = None,
    last_result: dict[str, Any] | None = None,
) -> None:
    summary = None
    if last_result:
        summary = {
            "run_id": last_result.get("run_id"),
            "status": last_result.get("status"),
            "task_type": last_result.get("task_type"),
            "output_paths": last_result.get("output_paths", {}),
            "errors": last_result.get("errors", []),
        }
    existing = load_session(session_id)
    payload = {
        "session_id": session_id,
        "title": _session_title(messages) if messages else existing.get("title", "New chat"),
        "created_at": existing.get("created_at") or datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "messages": messages,
        "pending_insert": pending_insert,
        "last_result": summary,
    }
    _session_path(session_id).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    set_active_session_id(session_id)


def list_sessions() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for path in sessions_dir().glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            out.append(
                {
                    "session_id": path.stem,
                    "title": data.get("title") or path.stem,
                    "updated_at": data.get("updated_at", ""),
                    "message_count": len(data.get("messages") or []),
                }
            )
        except (json.JSONDecodeError, OSError):
            continue
    out.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return out


def new_session() -> str:
    """Create a fresh chat session and make it active."""
    session_id = create_session_id()
    empty = _empty_session(session_id)
    _session_path(session_id).write_text(json.dumps(empty, indent=2), encoding="utf-8")
    set_active_session_id(session_id)
    return session_id


def ensure_active_session() -> str:
    active = get_active_session_id()
    if active and _session_path(active).exists():
        return active
    return new_session()


def delete_session(session_id: str) -> None:
    path = _session_path(session_id)
    if path.exists():
        path.unlink()
    if get_active_session_id() == session_id:
        active_session_path().unlink(missing_ok=True)


# Legacy single-file API (migrate on first load)
def chat_history_path() -> Path:
    return _chat_root() / "chat_history.json"


def migrate_legacy_chat_if_needed() -> str | None:
    legacy = chat_history_path()
    if not legacy.exists():
        return None
    try:
        data = json.loads(legacy.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        legacy.unlink(missing_ok=True)
        return None
    if not data.get("messages"):
        legacy.unlink(missing_ok=True)
        return None
    sid = create_session_id()
    save_session(
        sid,
        data.get("messages") or [],
        pending_insert=data.get("pending_insert"),
        last_result=data.get("last_result"),
    )
    legacy.rename(legacy.with_suffix(".json.migrated"))
    return sid


def clear_chat_file() -> None:
    """Remove active session file (prefer delete_session / new_session)."""
    active = get_active_session_id()
    if active:
        delete_session(active)
