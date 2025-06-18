"""Utility for turning PDF files into LangChain document chunks."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import List

from google.cloud import storage
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from pdfminer.high_level import extract_text


class OCRRequiredError(Exception):
    """Raised when the PDF has no extractable text and OCR is needed."""

class DocumentProcessorError(Exception):
    """Base exception for document processing errors."""

class GCSConnectionError(DocumentProcessorError):
    """Raised when there's an issue with GCS connection or operations."""

class FileProcessingError(DocumentProcessorError):
    """Raised for general file processing issues."""


class DocumentProcessor:
    """Process local or GCS PDF files into text chunks."""

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        gcs_project_id: str | None = None
    ) -> None:
        """Initialize the processor with optional chunk configuration and GCS project ID."""
        self.chunk_size = (
            int(os.environ.get("MAX_CHUNK_SIZE", 500))
            if chunk_size is None
            else chunk_size
        )
        self.chunk_overlap = (
            int(os.environ.get("CHUNK_OVERLAP", 50))
            if chunk_overlap is None
            else chunk_overlap
        )
        self.gcs_project_id = gcs_project_id or os.environ.get("GCP_PROJECT_ID")

        # Initialize storage client in constructor
        if self.gcs_project_id: # Only attempt to initialize if project_id is available
            try:
                self.storage_client = storage.Client(project=self.gcs_project_id)
            except Exception as e:
                # Allowing DocumentProcessor to be instantiated even if GCS client fails,
                # as it might only be used for local files. GCS operations will fail later if client is None.
                self.storage_client = None
                print(f"Warning: Failed to initialize GCS client for project '{self.gcs_project_id}': {e}. GCS operations will not be available.")
        else:
            self.storage_client = None
            print("Warning: GCP_PROJECT_ID not set. GCS operations will not be available for DocumentProcessor.")

    def _ensure_text(self, file_path: str) -> None:
        """Ensure the PDF contains extractable text."""
        try:
            # Limit text extraction to a few pages to speed up check
            text = extract_text(file_path, maxpages=3)
        except Exception as e:
            raise FileProcessingError(f"Error extracting text from {file_path} for check: {e}")
        if not text or not text.strip():
            raise OCRRequiredError(f"PDF {file_path} contains no extractable text and may require OCR.")

    def _process_local_pdf(self, file_path: str, original_source: str) -> List[Document]:
        """Loads a local PDF file and splits it into chunks."""
        self._ensure_text(file_path)
        loader = PyPDFLoader(file_path)
        try:
            docs = loader.load()
        except Exception as e:
            raise FileProcessingError(f"Error loading PDF {file_path} with PyPDFLoader: {e}")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        chunks = splitter.split_documents(docs)

        for i, doc in enumerate(chunks):
            doc.metadata["source"] = original_source # Use original GCS URI or local path
            doc.metadata["chunk_index"] = i
        return chunks

    def process(self, file_path_or_uri: str) -> List[Document]:
        """Load a PDF file from a local path or GCS URI and split it into chunks."""
        if file_path_or_uri.startswith("gs://"):
            if not self.storage_client:
                raise GCSConnectionError("GCS client not available. Ensure GCP_PROJECT_ID is set and client initialized successfully.")

            try:
                bucket_name, blob_name = file_path_or_uri[5:].split("/", 1)
                # Use the initialized client instance
                bucket = self.storage_client.bucket(bucket_name)
                blob = bucket.blob(blob_name)

                if not blob.exists():
                    raise FileNotFoundError(f"GCS object not found: {file_path_or_uri}")

                if not blob.name.lower().endswith(".pdf"):
                    raise ValueError("Only .pdf files are supported from GCS.")

                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                    try:
                        blob.download_to_filename(tmp_file.name)
                        return self._process_local_pdf(tmp_file.name, original_source=file_path_or_uri)
                    finally:
                        os.remove(tmp_file.name) # Ensure cleanup
            except GCSConnectionError: # Re-raise specific GCS errors
                raise
            except FileNotFoundError: # Re-raise
                raise
            except ValueError: # Re-raise
                raise
            except Exception as e: # Catch other GCS or tempfile issues
                raise GCSConnectionError(f"Error processing GCS file {file_path_or_uri}: {e}")
        else:
            path = Path(file_path_or_uri)
            if path.suffix.lower() != ".pdf":
                raise ValueError("Only .pdf files are supported for local files.")
            if not path.is_file():
                raise FileNotFoundError(f"Local file not found: {file_path_or_uri}")
            return self._process_local_pdf(str(path), original_source=file_path_or_uri)
