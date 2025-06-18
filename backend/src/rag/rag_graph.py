from __future__ import annotations

import os
from typing import TYPE_CHECKING, TypedDict, List

from google.cloud import storage
from langgraph.graph import StateGraph, END

if TYPE_CHECKING:
    from langchain_core.runnables import RunnableConfig
    # OverallState might not be directly used by rag_load_data_from_gcs,
    # but create_rag_graph_runnable is part of the main agent's graph structure.
    from agent.state import OverallState
    from rag.document_processor import DocumentProcessor
    from rag.vector_store import HybridVectorStore

class RagGraphState(TypedDict):
    """State specific to the RAG graph operations."""
    documents_processed_from_gcs: int
    gcs_bucket_name: str | None # Can be set via input to the graph
    error_messages: List[str]


def rag_load_data_from_gcs(state: RagGraphState, config: RunnableConfig) -> RagGraphState:
    """
    Scans a GCS bucket for PDF documents, processes them, and adds them to a vector store.
    This node expects 'document_processor' and 'vector_store' to be in config.configurable.
    """
    print("--- Starting RAG: Load data from GCS ---")
    document_processor: DocumentProcessor | None = config["configurable"].get("document_processor")
    vector_store: HybridVectorStore | None = config["configurable"].get("vector_store")

    gcp_project_id = os.getenv("GCP_PROJECT_ID")
    # RAG_GCS_BUCKET_NAME can be passed in state or fetched from env if not in state
    gcs_bucket_name = state.get("gcs_bucket_name") or os.getenv("RAG_GCS_BUCKET_NAME")

    # Initialize error_messages if not present
    current_errors = state.get("error_messages", [])

    if not document_processor or not vector_store:
        error_msg = "DocumentProcessor or HybridVectorStore not provided in config."
        print(f"Error: {error_msg}")
        # Ensure state is well-formed for return
        return {"documents_processed_from_gcs": 0, "gcs_bucket_name": gcs_bucket_name, "error_messages": current_errors + [error_msg]}

    if not gcp_project_id:
        error_msg = "GCP_PROJECT_ID environment variable not set."
        print(f"Error: {error_msg}")
        return {"documents_processed_from_gcs": 0, "gcs_bucket_name": gcs_bucket_name, "error_messages": current_errors + [error_msg]}

    if not gcs_bucket_name:
        error_msg = "RAG_GCS_BUCKET_NAME not set in environment or provided in state."
        print(f"Error: {error_msg}")
        return {"documents_processed_from_gcs": 0, "gcs_bucket_name": gcs_bucket_name, "error_messages": current_errors + [error_msg]}

    processed_count = 0
    try:
        # Ensure DocumentProcessor has project_id if not already set (e.g. if instantiated with default)
        if not document_processor.gcs_project_id:
            document_processor.gcs_project_id = gcp_project_id

        storage_client = storage.Client(project=gcp_project_id) # Use the one from DocumentProcessor or instantiate new? For listing, new is fine.
        blobs = storage_client.list_blobs(gcs_bucket_name)
        print(f"Scanning GCS bucket: {gcs_bucket_name} in project {gcp_project_id}")

        for blob in blobs:
            if blob.name.lower().endswith(".pdf"):
                gcs_uri = f"gs://{gcs_bucket_name}/{blob.name}"
                print(f"Processing document: {gcs_uri}")
                try:
                    chunks = document_processor.process(gcs_uri)
                    if chunks:
                        vector_store.add_documents(chunks, tier="cold") # Storing RAG docs in cold tier
                        print(f"Added {len(chunks)} chunks from {gcs_uri} to vector store (cold tier).")
                        processed_count += 1
                    else:
                        print(f"No chunks generated for {gcs_uri}.")
                except Exception as e: # Catch errors for individual document processing
                    error_msg = f"Failed to process document {gcs_uri}: {e}"
                    print(f"Error: {error_msg}")
                    current_errors.append(error_msg)
            else:
                print(f"Skipping non-PDF file: {blob.name}")

        if processed_count > 0:
            # vector_store.persist() # Chroma persistence is handled by its own mechanism if configured.
            # PGVector doesn't have a separate persist call like this.
            print(f"Processed {processed_count} documents. Vector store operations are typically auto-persisted or managed by their own configs.")

    except Exception as e: # Catch errors for GCS listing or client init
        error_msg = f"Error listing blobs or during GCS operations for bucket {gcs_bucket_name}: {e}"
        print(f"Error: {error_msg}")
        current_errors.append(error_msg)

    print(f"--- Finished RAG: Load data from GCS. Processed {processed_count} documents. Errors: {len(current_errors)} ---")
    return {"documents_processed_from_gcs": processed_count, "gcs_bucket_name": gcs_bucket_name, "error_messages": current_errors}


def create_rag_graph_runnable(
    document_processor_instance: DocumentProcessor,
    vector_store_instance: HybridVectorStore
) -> StateGraph:
    """
    Creates a runnable LangGraph StateGraph for the RAG pipeline.
    This function is intended to be called from the main agent graph setup,
    passing in the shared instances of DocumentProcessor and HybridVectorStore.
    """
    workflow = StateGraph(RagGraphState)
    # The node's function (rag_load_data_from_gcs) will receive the full RagGraphState
    # and the config. The config will have 'document_processor' and 'vector_store'
    # pre-configured by the .compile() call below.
    workflow.add_node("load_documents_from_gcs", rag_load_data_from_gcs)
    workflow.set_entry_point("load_documents_from_gcs")
    workflow.add_edge("load_documents_from_gcs", END)

    # Compile the graph, providing the actual instances that will be fixed
    # in the configuration for the node(s) within this subgraph.
    rag_graph_runnable = workflow.compile(
        checkpointer=None, # Add checkpointer if state needs to be persisted across RAG runs
        configurable={
            "document_processor": document_processor_instance,
            "vector_store": vector_store_instance,
        }
    )
    return rag_graph_runnable
