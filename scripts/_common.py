"""Shared test runner utilities."""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure project root on path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def setup_env(mock: bool = True, chapters: int | None = None) -> None:
    if mock and not os.environ.get("OPENAI_API_KEY"):
        os.environ["MOCK_LLM"] = "true"
    from config import get_settings
    get_settings.cache_clear()


def run_and_report(user_input: str, label: str) -> dict:
    setup_env()
    from graph.workflow import run_workflow
    from evals.run_evals import run_all_evals, write_markdown_report

    print(f"\n=== {label} ===\n")
    result = run_workflow(user_input)
    run_id = result.get("run_id", "")
    print(f"Run ID: {run_id}")
    print(f"Status: {result.get('status')}")
    print(f"Outputs: {result.get('output_paths')}")
    if run_id:
        report = run_all_evals(run_id)
        write_markdown_report(run_id, report)
        print(f"Eval overall: {report.get('overall_score')}")
    return result
