from __future__ import annotations

import os
import tempfile
from typing import List, Optional

from fastapi import APIRouter, Depends, File, UploadFile, Request
from pydantic import BaseModel
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader


class DocumentProcessor:
    """Simple PDF processor that splits documents into chunks."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200) -> None:
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )

    def process(self, file_path: str) -> List[Document]:
        """Load a PDF file and return split documents."""
        reader = PdfReader(file_path)
        docs: List[Document] = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            docs.append(
                Document(
                    page_content=text,
                    metadata={"page": i + 1, "source": os.path.basename(file_path)},
                )
            )
        return self.splitter.split_documents(docs)


class HybridVectorStore:
    """Very small in-memory vector store using TF-IDF."""

    def __init__(self) -> None:
        from sklearn.feature_extraction.text import TfidfVectorizer

        self.vectorizer = TfidfVectorizer()
        self.documents: List[Document] = []
        self._matrix = None

    def add_documents(self, docs: List[Document]) -> None:
        self.documents.extend(docs)
        texts = [d.page_content for d in self.documents]
        self._matrix = self.vectorizer.fit_transform(texts)

    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        if not self.documents:
            return []
        from sklearn.metrics.pairwise import cosine_similarity

        query_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self._matrix).flatten()
        indices = sims.argsort()[::-1][:k]
        return [self.documents[i] for i in indices]


router = APIRouter(prefix="/api/documents", tags=["documents"])


class QueryRequest(BaseModel):
    query: str
    k: Optional[int] = 4


def get_processor(request: Request) -> DocumentProcessor:
    return request.app.state.processor


def get_store(request: Request) -> HybridVectorStore:
    return request.app.state.store


@router.post("/upload")
async def upload_documents(
    files: List[UploadFile] = File(...),
    processor: DocumentProcessor = Depends(get_processor),
    store: HybridVectorStore = Depends(get_store),
):
    results = []
    for file in files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            data = await file.read()
            tmp.write(data)
            tmp_path = tmp.name
        docs = processor.process(tmp_path)
        store.add_documents(docs)
        os.remove(tmp_path)
        results.append({"filename": file.filename, "chunks": len(docs)})
    return results


@router.post("/query")
async def query_documents(
    request: QueryRequest,
    store: HybridVectorStore = Depends(get_store),
):
    docs = store.similarity_search(request.query, request.k or 4)
    return [
        {"page_content": d.page_content, "metadata": d.metadata}
        for d in docs
    ]


