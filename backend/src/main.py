from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from agent.app import create_frontend_router
from api.documents import (
    router as documents_router,
    DocumentProcessor,
    HybridVectorStore,
    get_processor,
    get_store,
)


@asynccontextmanager
def lifespan(app: FastAPI):
    """Create shared resources for the application."""
    processor = DocumentProcessor()
    store = HybridVectorStore()
    app.dependency_overrides[get_processor] = lambda: processor
    app.dependency_overrides[get_store] = lambda: store
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(documents_router)
app.mount("/app", create_frontend_router(), name="frontend")
