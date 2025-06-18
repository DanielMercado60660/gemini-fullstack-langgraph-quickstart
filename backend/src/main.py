from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends

from agent.app import create_frontend_router
from auth.firebase import initialize_firebase_app, verify_firebase_token
from api.documents import (
    router as documents_router,
    DocumentProcessor,
    HybridVectorStore,
    get_processor,
    get_store,
)
from rag.embeddings import EmbeddingService
from agent.graph import create_main_graph_runnable # Import the new graph constructor


# The main agent graph runnable instance
# This will be created during lifespan startup.
main_agent_graph = None

@asynccontextmanager
async def lifespan(app: FastAPI): # Mark lifespan as async
    """Create shared resources for the application."""
    global main_agent_graph
    initialize_firebase_app()  # Initialize Firebase Admin SDK

    # Initialize EmbeddingService
    embedding_service = EmbeddingService() # Assumes ENV vars are set

    # Initialize DocumentProcessor
    # Pass gcs_project_id if it's available and needed at init, or it will use ENV
    processor = DocumentProcessor()

    # Initialize HybridVectorStore
    store = HybridVectorStore(embedding_function=embedding_service.embed_texts)

    app.dependency_overrides[get_processor] = lambda: processor
    app.dependency_overrides[get_store] = lambda: store

    # Create the main agent graph runnable
    main_agent_graph = create_main_graph_runnable(
        document_processor=processor,
        vector_store=store
    )
    print("Main agent graph created.")

    yield

    # Clean up resources if needed on shutdown
    print("Application shutdown.")


app = FastAPI(lifespan=lifespan)

# Example of how the graph might be exposed or used by other parts of the app
# For instance, if you have an endpoint that runs the agent:
# from agent.state import OverallState
# @app.post("/invoke-agent/")
# async def invoke_agent_endpoint(initial_state: OverallState, current_user: dict = Depends(verify_firebase_token)):
#     if main_agent_graph is None:
#         raise HTTPException(status_code=503, detail="Agent graph not initialized")
#     # Config for the graph run, could include user_id from token
#     config = {"configurable": {"user_id": current_user["uid"]}}
#     # Add other necessary fields to initial_state like 'messages', 'use_documents', 'rag_gcs_bucket_name'
#     async for event in main_agent_graph.astream_events(initial_state, config=config, version="v1"):
#         # Stream events or process final result
#         pass
#     return {"status": "done"}


app.include_router(
    documents_router,
    dependencies=[Depends(verify_firebase_token)] # Protect the /documents/ endpoint
)
app.mount("/app", create_frontend_router(), name="frontend")
