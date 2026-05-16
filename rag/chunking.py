"""Document chunking for RAG."""
from config import get_settings


def chunk_text(text: str, chunk_size: int | None = None, overlap: int | None = None) -> list[str]:
    settings = get_settings()
    size = chunk_size or settings.chunk_size
    ov = overlap or settings.chunk_overlap
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - ov
        if start >= len(text):
            break
    return [c.strip() for c in chunks if c.strip()]
