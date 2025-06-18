"""Shared state definitions for the agent graphs."""
from __future__ import annotations

import operator
from dataclasses import dataclass, field
from typing import TypedDict

from langgraph.graph import add_messages
from typing_extensions import Annotated


class OverallState(TypedDict):
    """State shared across the whole agent run."""
    messages: Annotated[list, add_messages]
    search_query: Annotated[list, operator.add]
    web_research_result: Annotated[list, operator.add]
    sources_gathered: Annotated[list, operator.add]
    initial_search_query_count: int
    max_research_loops: int
    research_loop_count: int
    reasoning_model: str
    use_documents: bool


class ReflectionState(TypedDict):
    """State produced by the reflection step."""
    is_sufficient: bool
    knowledge_gap: str
    follow_up_queries: Annotated[list, operator.add]
    research_loop_count: int
    number_of_ran_queries: int


class Query(TypedDict):
    """Represents a single search query."""
    query: str
    rationale: str


class QueryGenerationState(TypedDict):
    """State containing generated queries."""
    query_list: list[Query]


class WebSearchState(TypedDict):
    """State for a single web search."""
    search_query: str
    id: str


@dataclass(kw_only=True)
class SearchStateOutput:
    """Output after the full search cycle."""
    running_summary: str = field(default=None)  # Final report
