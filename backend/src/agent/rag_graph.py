"""Minimal RAG sub-graph."""
from __future__ import annotations

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from .state import OverallState


def retrieve_documents(state: OverallState, config: RunnableConfig) -> OverallState:
    """Return an empty answer string."""
    return {"messages": [AIMessage(content="")]}  # pragma: no cover



def create_rag_graph():
    """Return a minimal RAG sub-graph."""
    builder = StateGraph(OverallState)
    builder.add_node("retrieve_documents", retrieve_documents)
    builder.add_edge(START, "retrieve_documents")
    builder.add_edge("retrieve_documents", END)
    return builder.compile(name="rag-sub-graph")
