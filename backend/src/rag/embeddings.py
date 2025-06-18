"""Utilities for embedding models."""

import os
from __future__ import annotations

import vertexai
from vertexai.language_models import TextEmbeddingModel, TextEmbeddingInput

# Consider making GCP_LOCATION an environment variable if it needs to be flexible
GCP_LOCATION = "us-central1"

class ConfigError(Exception):
    """Raised when environment configuration is invalid or missing."""

class EmbeddingService:
    """Service for embedding text using Vertex AI."""

    def __init__(self, model_name: str | None = None, project_id: str | None = None, location: str | None = None) -> None:
        """Initialize the service.

        Args:
            model_name: Name of the Vertex AI embedding model. If ``None``, the
                environment variable ``EMBEDDING_MODEL_NAME`` is used.
            project_id: Google Cloud Project ID. If ``None``, the
                environment variable ``GCP_PROJECT_ID`` is used.
            location: Google Cloud region for Vertex AI. If ``None``, the
                environment variable ``GCP_LOCATION`` is used, falling back to GCP_LOCATION global.
        """
        self.project_id = project_id or os.environ.get("GCP_PROJECT_ID")
        self.location = location or os.environ.get("GCP_LOCATION", GCP_LOCATION)
        self.model_name = model_name or os.environ.get("EMBEDDING_MODEL_NAME")

        if not self.project_id:
            raise ConfigError("GCP_PROJECT_ID is not set.")
        if not self.model_name:
            raise ConfigError("EMBEDDING_MODEL_NAME is not set.")
        if not self.location:
            raise ConfigError("GCP_LOCATION is not set.")

        try:
            vertexai.init(project=self.project_id, location=self.location)
            # Test connection / model existence early
            self._model = TextEmbeddingModel.from_pretrained(self.model_name)
        except Exception as e:
            raise ConfigError(f"Failed to initialize Vertex AI or load model '{self.model_name}': {e}") from e


    def embed_texts(self, texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
        """Embed a batch of texts using Vertex AI.

        Args:
            texts: A list of texts to embed.
            task_type: The task type for the embedding. Common types include:
                       "RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY", "SEMANTIC_SIMILARITY",
                       "CLASSIFICATION", "CLUSTERING".

        Returns:
            A list of embedding vectors (each a list of floats).

        Raises:
            Exception: If embedding fails.
        """
        if not texts:
            return []

        try:
            # SDK expects a list of TextEmbeddingInput objects
            inputs = [TextEmbeddingInput(text, task_type) for text in texts]
            embeddings = self._model.get_embeddings(inputs)
            return [embedding.values for embedding in embeddings]
        except Exception as e:
            # Log the error or handle it more gracefully
            print(f"Error embedding texts with model {self.model_name}: {e}")
            # Depending on requirements, you might re-raise, return empty, or a specific error object
            raise


    @property
    def dimension(self) -> int | None:
        """Return embedding dimension for the configured model.

        Note: This might not be perfectly accurate for all models or future models.
        It's often better to get the dimension from an actual embedding if possible.
        """
        # Common known dimensions. This might need to be updated or fetched dynamically.
        # For some models, the dimension is fixed and documented.
        model_to_dimension = {
            "textembedding-gecko@001": 768,
            "textembedding-gecko@latest": 768,
            "textembedding-gecko-multilingual@latest": 768,
            "text-embedding-preview-0409": 768, # older model
            "text-multilingual-embedding-preview-0409": 768, # older model
            # Add other models and their dimensions as needed
            # Newer models like text-embedding-004 also have 768
        }
        # A more robust way if the model instance has dimension info (not standard for TextEmbeddingModel)
        # if hasattr(self._model, 'output_dimensionality'):
        # return self._model.output_dimensionality

        # Fallback for common new models if not in map
        if "004" in self.model_name or "ada" in self.model_name: # older models might have ada
             return 768 # typical for newer Gecko models

        return model_to_dimension.get(self.model_name)
