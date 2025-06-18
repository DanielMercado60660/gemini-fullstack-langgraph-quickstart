"""Utility for turning PDF files into LangChain document chunks."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from pdfminer.high_level import extract_text


class OCRRequiredError(Exception):
    """Raised when the PDF has no extractable text and OCR is needed."""


class DocumentProcessor:
    """Process local PDF files into text chunks."""

    def __init__(
        self, chunk_size: int | None = None, chunk_overlap: int | None = None
    ) -> None:
        """Initialize the processor with optional chunk configuration."""
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

    def _ensure_text(self, file_path: str) -> None:
        """Ensure the PDF contains extractable text."""
        try:
            text = extract_text(file_path, maxpages=1)
        except Exception:
            text = ""
        if not text or not text.strip():
            raise OCRRequiredError("PDF contains no extractable text and requires OCR")

    def process(self, file_path: str) -> List[Document]:
        """Load a PDF file and split it into chunks."""
        path = Path(file_path)
        if path.suffix.lower() != ".pdf":
            raise ValueError("Only .pdf files are supported")
        if not path.is_file():
            raise FileNotFoundError(str(path))

        self._ensure_text(str(path))

        loader = PyPDFLoader(str(path))
        docs = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        chunks = splitter.split_documents(docs)

        for i, doc in enumerate(chunks):
            doc.metadata["source"] = str(path)
            doc.metadata["chunk_index"] = i
        return chunks
