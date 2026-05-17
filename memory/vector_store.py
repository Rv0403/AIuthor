"""ChromaDB vector store wrapper."""
from __future__ import annotations

from typing import Any

from config import get_settings


class VectorStore:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        settings = get_settings()
        self._client = None
        self._collection = None
        self._persist_dir = str(settings.chroma_dir)

    def _ensure_client(self) -> None:
        if self._client is not None:
            return
        import chromadb

        self._client = chromadb.PersistentClient(path=self._persist_dir)
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(self, ids: list[str], texts: list[str], metadatas: list[dict[str, Any]] | None = None) -> None:
        self._ensure_client()
        embeddings = self._embed(texts, task_type="RETRIEVAL_DOCUMENT")
        self._collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas or [{}] * len(texts),
        )

    def query(self, query_text: str, top_k: int | None = None) -> list[dict[str, Any]]:
        self._ensure_client()
        settings = get_settings()
        k = top_k or settings.rag_top_k
        embedding = self._embed([query_text], task_type="RETRIEVAL_QUERY")[0]
        results = self._collection.query(query_embeddings=[embedding], n_results=k)
        docs = []
        if results and results.get("documents"):
            for i, doc in enumerate(results["documents"][0]):
                meta = (results.get("metadatas") or [[]])[0]
                meta_i = meta[i] if i < len(meta) else {}
                dist = (results.get("distances") or [[]])[0]
                docs.append(
                    {
                        "text": doc,
                        "metadata": meta_i,
                        "score": 1.0 - (dist[i] if i < len(dist) else 0),
                    }
                )
        return docs

    def _embed_gemini(self, texts: list[str], *, task_type: str | None = None) -> list[list[float]]:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY required for embeddings")
        from google import genai
        from google.genai import types

        model = settings.embedding_model.removeprefix("models/")
        client = genai.Client(api_key=settings.gemini_api_key)
        config = types.EmbedContentConfig(task_type=task_type) if task_type else None
        vectors: list[list[float]] = []
        for text in texts:
            resp = client.models.embed_content(
                model=model,
                contents=text,
                config=config,
            )
            emb = resp.embeddings[0]
            values = getattr(emb, "values", None) or emb
            vectors.append(list(values))
        return vectors

    def _embed(self, texts: list[str], *, task_type: str | None = None) -> list[list[float]]:
        settings = get_settings()
        if settings.mock_llm:
            import hashlib

            return [[float(int(hashlib.md5(t.encode()).hexdigest()[:8], 16) % 1000) / 1000.0] * 64 for t in texts]

        return self._embed_gemini(texts, task_type=task_type)
