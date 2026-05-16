"""Persistent memory store per run."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config import get_settings
from memory.schemas import BookMemory, MemorySnapshot


class MemoryStore:
    def __init__(self, run_id: str):
        self.run_id = run_id
        settings = get_settings()
        self.run_dir = settings.outputs_dir / run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.memory_path = self.run_dir / "memory.json"
        self.snapshot_path = self.run_dir / "snapshot.json"

    def load_memory(self) -> BookMemory:
        if self.memory_path.exists():
            data = json.loads(self.memory_path.read_text(encoding="utf-8"))
            return BookMemory.model_validate(data)
        return BookMemory()

    def save_memory(self, memory: BookMemory) -> None:
        self.memory_path.write_text(
            memory.model_dump_json(indent=2),
            encoding="utf-8",
        )

    def save_snapshot(
        self,
        memory: BookMemory,
        outline: dict[str, Any] | None,
        chapters: list[dict[str, Any]],
        brief: dict[str, Any] | None,
    ) -> None:
        snap = MemorySnapshot(
            run_id=self.run_id,
            memory=memory,
            outline=outline,
            chapters=chapters,
            brief=brief,
        )
        self.snapshot_path.write_text(
            snap.model_dump_json(indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load_snapshot(cls, run_id: str) -> MemorySnapshot | None:
        settings = get_settings()
        path = settings.outputs_dir / run_id / "snapshot.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return MemorySnapshot.model_validate(data)

    @classmethod
    def list_runs(cls) -> list[str]:
        settings = get_settings()
        if not settings.outputs_dir.exists():
            return []
        runs = [p for p in settings.outputs_dir.iterdir() if p.is_dir() and (p / "snapshot.json").exists()]
        runs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return [p.name for p in runs]
