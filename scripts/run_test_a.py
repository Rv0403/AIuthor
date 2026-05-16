"""Test A: 10-chapter personal finance guide, Conversational tone."""
from scripts._common import run_and_report

if __name__ == "__main__":
    # Use full brief; set MOCK_LLM=true for quick offline validation (2 chapters in mock planner)
    run_and_report(
        "A 10-chapter beginner's guide to personal finance, Conversational tone, approximately 2500 words per chapter",
        "Test A",
    )
