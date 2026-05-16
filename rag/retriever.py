"""Hybrid RAG retrieval: dense + BM25."""
from __future__ import annotations

from typing import Any

from config import get_settings
from memory.vector_store import VectorStore


class RAGRetriever:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.vector_store = VectorStore(collection_name)
        self._bm25 = None
        self._bm25_corpus: list[str] = []

    def retrieve(self, query: str, top_k: int | None = None) -> list[dict[str, Any]]:
        settings = get_settings()
        k = top_k or settings.rag_top_k

        dense = self.vector_store.query(query, top_k=k * 2)
        if not self._bm25_corpus:
            self._bm25_corpus = [d["text"] for d in dense]
            if self._bm25_corpus:
                from rank_bm25 import BM25Okapi

                tokenized = [doc.lower().split() for doc in self._bm25_corpus]
                self._bm25 = BM25Okapi(tokenized)

        if self._bm25 and self._bm25_corpus:
            scores = self._bm25.get_scores(query.lower().split())
            bm25_hits = sorted(
                zip(self._bm25_corpus, scores),
                key=lambda x: x[1],
                reverse=True,
            )[:k]
            merged: dict[str, dict[str, Any]] = {}
            for doc in dense:
                merged[doc["text"][:200]] = {**doc, "dense_score": doc.get("score", 0)}
            for text, score in bm25_hits:
                key = text[:200]
                if key in merged:
                    merged[key]["bm25_score"] = float(score)
                    merged[key]["score"] = merged[key].get("dense_score", 0) * 0.6 + float(score) * 0.4
                else:
                    merged[key] = {"text": text, "bm25_score": float(score), "score": float(score) * 0.4}
            results = sorted(merged.values(), key=lambda x: x.get("score", 0), reverse=True)
            return results[:k]

        return dense[:k]
