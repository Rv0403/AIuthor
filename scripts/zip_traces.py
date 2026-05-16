"""Zip trace bundle for a run (submission artifact)."""
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import get_settings


def main():
    run_id = sys.argv[1] if len(sys.argv) > 1 else None
    if not run_id:
        print("Usage: python -m scripts.zip_traces <run_id>")
        sys.exit(1)
    trace_dir = get_settings().traces_dir / run_id
    if not trace_dir.exists():
        print(f"No traces at {trace_dir}")
        sys.exit(1)
    out = get_settings().outputs_dir / run_id / f"traces_{run_id}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in trace_dir.glob("*"):
            zf.write(f, arcname=f.name)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
