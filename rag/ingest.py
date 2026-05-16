"""Ingest documents into ChromaDB."""
from pathlib import Path

from config import get_settings
from memory.vector_store import VectorStore
from rag.chunking import chunk_text


def ingest_corpus(collection_name: str, source_dir: Path | None = None) -> int:
    settings = get_settings()
    src = source_dir or settings.rag_corpus_dir
    src.mkdir(parents=True, exist_ok=True)

    store = VectorStore(collection_name)
    count = 0
    for path in src.glob("**/*"):
        if path.suffix.lower() not in {".txt", ".md"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        chunks = chunk_text(text)
        if not chunks:
            continue
        ids = [f"{path.stem}_{i}" for i in range(len(chunks))]
        metas = [{"source": str(path), "chunk": i} for i in range(len(chunks))]
        store.add_documents(ids, chunks, metas)
        count += len(chunks)
    return count
