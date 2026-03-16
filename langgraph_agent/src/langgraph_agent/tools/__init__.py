"""Tools for the executor node."""

from langgraph_agent.tools.search import get_search_tool, web_search
from langgraph_agent.tools.deep_research import get_deep_research_tool, deep_research_stock

__all__ = [
    "web_search",
    "get_search_tool",
    "deep_research_stock",
    "get_deep_research_tool",
]
