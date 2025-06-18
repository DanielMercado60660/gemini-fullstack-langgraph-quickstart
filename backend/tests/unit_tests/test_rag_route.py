import os

from langchain_core.messages import HumanMessage

os.environ.setdefault("GEMINI_API_KEY", "dummy")
from agent import graph


def test_use_documents_routs_to_rag():
    state = {
        "messages": [HumanMessage(content="test")],
        "search_query": [],
        "web_research_result": [],
        "sources_gathered": [],
        "initial_search_query_count": 0,
        "max_research_loops": 0,
        "research_loop_count": 0,
        "reasoning_model": "",
        "use_documents": True,
    }

    result = graph.invoke(state)
    assert result["messages"][-1].content == ""
