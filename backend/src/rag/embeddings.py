
"""Utilities for embedding models."""


class ConfigError(Exception):
    """Raised when environment configuration is invalid."""

import os
from __future__ import annotations
#This may need to be updated REVIEWME
"""Create and handle embeddings for documents."""

class ConfigError(Exception):
    """Raised when required configuration is missing."""


class EmbeddingService:
    """Service for embedding text using Vertex AI."""

    def __init__(self, model_name: str | None = None) -> None:
        """Initialize the service.

        Args:
            model_name: Name of the Vertex AI embedding model. If ``None`` the
                environment variable ``EMBEDDING_MODEL`` is used.
        """
        self.model_name = model_name or os.environ.get("EMBEDDING_MODEL")
        if self.model_name is None:
            raise ConfigError("EMBEDDING_MODEL is not set")

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts using Vertex AI."""
        project_id = os.environ.get("GCP_PROJECT_ID")
        if not project_id or not self.model_name:
            raise ConfigError("Missing EMBEDDING_MODEL or GCP_PROJECT_ID")
        raise NotImplementedError("Embedding call to Vertex AI not implemented")

    @property
    def dimension(self) -> int | None:
        """Return embedding dimension for the configured model."""
        if self.model_name == "gemini-embedding-001":
            return 3072
        if self.model_name == "text-embedding-005":
            return 768
        return None




pass
main
