"""Test C: Regenerate chapter 3 in Academic, Motivational, Witty from Test A run."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts._common import setup_env, run_and_report
from memory.memory_store import MemoryStore


def main():
    setup_env()
    runs = MemoryStore.list_runs()
    if not runs:
        print("Run Test A first.")
        sys.exit(1)
    source = runs[0]
    for tone in ("Academic", "Motivational", "Witty"):
        run_and_report(
            f"Using run {source}, regenerate Chapter 3 in {tone} tone",
            f"Test C — {tone}",
        )


if __name__ == "__main__":
    main()
