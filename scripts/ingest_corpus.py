"""Ingest RAG corpus into ChromaDB."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rag.ingest import ingest_corpus


def main():
    collection = sys.argv[1] if len(sys.argv) > 1 else "default"
    count = ingest_corpus(collection)
    print(f"Ingested {count} chunks into collection '{collection}'")


if __name__ == "__main__":
    main()
