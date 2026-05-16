"""CLI entry point."""
import argparse
import sys

from graph.workflow import run_workflow


def main():
    parser = argparse.ArgumentParser(description="AIuthor book generation")
    parser.add_argument("prompt", nargs="?", default="A 2-chapter guide to personal finance in conversational tone")
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()
    result = run_workflow(args.prompt, run_id=args.run_id)
    print(f"Run ID: {result.get('run_id')}")
    print(f"Status: {result.get('status')}")
    print(f"Outputs: {result.get('output_paths')}")
    if result.get("errors"):
        print("Errors:", result["errors"], file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
