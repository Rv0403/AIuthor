"""Test D: Insert chapter between 4 and 5 — self-heal TOC, callbacks, glossary."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts._common import setup_env
from graph.workflow import run_workflow
from memory.memory_store import MemoryStore
from memory.repair import update_toc_manifest


def assert_repair(run_id: str) -> bool:
    snap = MemoryStore.load_snapshot(run_id)
    if not snap or not snap.outline:
        print("FAIL: no snapshot")
        return False
    chapters = snap.outline.get("chapters", [])
    nums = [c["chapter_number"] for c in chapters]
    if len(nums) != len(set(nums)):
        print("FAIL: duplicate chapter numbers", nums)
        return False
    toc = update_toc_manifest(snap.outline)
    if len(toc) != len(chapters):
        print("FAIL: TOC length mismatch", len(toc), len(chapters))
        return False
  # Check sequential numbering
    expected = list(range(1, len(chapters) + 1))
    if sorted(nums) != expected:
        print("FAIL: non-sequential chapters", sorted(nums))
        return False
    print("PASS: TOC and chapter numbering consistent")
    print(f"Chapters: {len(chapters)}, Callbacks: {len(snap.memory.callback_index)}, Glossary: {len(snap.memory.glossary_terms)}")
    return True


def main():
    setup_env()
    runs = MemoryStore.list_runs()
    if not runs:
        print("Run Test A first.")
        sys.exit(1)
    # Prefer run with the most chapters (latest full Test A)
    source = runs[0]
    best_count = 0
    for rid in runs[:5]:
        snap = MemoryStore.load_snapshot(rid)
        if snap and snap.outline:
            n = len(snap.outline.get("chapters", []))
            if n > best_count:
                best_count = n
                source = rid
    snap = MemoryStore.load_snapshot(source)
    max_ch = len(snap.outline.get("chapters", [])) if snap and snap.outline else 10
    insert_after = min(4, max(1, max_ch - 1))
    result = run_workflow(
        f"Insert a new chapter between Chapter {insert_after} and {insert_after + 1} in book run {source}",
        run_id=None,
    )
    run_id = result.get("run_id", "")
    print(f"Insert run: {run_id}")
    ok = assert_repair(run_id) if run_id else False
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
