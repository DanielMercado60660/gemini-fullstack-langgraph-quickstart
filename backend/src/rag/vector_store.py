"""Hybrid vector store combining Chroma and PGVector."""

from __future__ import annotations

import os
from typing import List, Literal

from langchain_community.vectorstores import Chroma, PGVector
from langchain_core.documents import Document

from .embeddings import ConfigError


class HybridVectorStore:
    """Wrapper around two vector stores for hot and cold tiers."""

    def __init__(self, embedding_function):
        """Initialize the hot and cold vector stores."""
        persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        self._hot_store = Chroma(
            persist_directory=persist_dir,
            embedding_function=embedding_function,
        )
        database_url = os.getenv("DATABASE_URL")
        self._cold_store = (
            PGVector(connection_string=database_url, embedding_function=embedding_function)
            if database_url
            else None
        )

    def add_documents(
        self, docs: List[Document], tier: Literal["hot", "cold"] = "hot"
    ) -> None:
        """Add documents to one of the stores."""
        if tier == "hot":
            self._hot_store.add_documents(docs)
        else:
            if self._cold_store is None:
                raise ConfigError("DATABASE_URL is not configured")
            self._cold_store.add_documents(docs)

    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """Search the hot store first, then cold store if needed."""
        results = self._hot_store.similarity_search(query, k=k)
        if len(results) >= k:
            return results[:k]
        remaining = k - len(results)
        if self._cold_store is None:
            return results
        cold_results = self._cold_store.similarity_search(query, k=remaining)
        return results + cold_results

    def persist(self) -> None:
        """Persist the hot store."""
        self._hot_store.persist()
