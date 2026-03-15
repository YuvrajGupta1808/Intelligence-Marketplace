"""Web search tool (Google-style) for the executor."""

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool


def _get_search_run():
    return DuckDuckGoSearchRun()


@tool
def web_search(query: str) -> str:
    """Search the web (Google-style) for current information. Use this when you need to look up facts, news, or any information on the internet. Input should be a clear search query string."""
    return _get_search_run().invoke(query)


def get_search_tool():
    """Return the web search tool for binding to the executor LLM."""
    return web_search
