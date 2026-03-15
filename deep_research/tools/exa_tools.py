"""
EXA web search tools for the deep finance research agent.
Uses EXA API for neural search and full-page content extraction.
When EXA_API_KEY is set, exa_web_search returns links and snippets; exa_get_contents
fetches full page text for selected URLs. For SEC.gov or JS-heavy sites, use Unbrowse.
"""
from __future__ import annotations

import os
from typing import Optional

from langchain_core.tools import tool


def _get_exa_client():
    """Return Exa client or None if EXA_API_KEY is not set."""
    try:
        from exa_py import Exa
    except ImportError:
        return None
    key = os.getenv("EXA_API_KEY", "").strip()
    if not key:
        return None
    return Exa(api_key=key)


@tool
def exa_web_search(
    query: str,
    num_results: int = 10,
    include_domains: Optional[str] = None,
) -> str:
    """
    Search the web using EXA (neural search). Returns titles, URLs, and snippets for each result.

    Use for detailed online research: industry data, competitors, market size, recent news,
    macro trends. Then use exa_get_contents on selected URLs for full page text, or use
    Unbrowse for SEC.gov and JS-heavy/authenticated sites.

    Args:
        query: Natural-language search query (e.g. "Apple Inc competitive position in smartphones 2024").
        num_results: Max results to return (default 10).
        include_domains: Optional comma-separated domains to restrict search (e.g. "reuters.com,bloomberg.com").

    Returns:
        Formatted string with each result: title, URL, snippet. Or error message if EXA is not configured.
    """
    exa = _get_exa_client()
    if exa is None:
        return (
            "EXA is not configured. Set EXA_API_KEY in .env for web search. "
            "Use Unbrowse and live_finance_researcher for research without EXA."
        )
    try:
        kwargs = {"query": query, "num_results": min(num_results, 20), "contents": False}
        if include_domains:
            kwargs["include_domains"] = [d.strip() for d in include_domains.split(",") if d.strip()]
        response = exa.search(**kwargs)
        results = getattr(response, "results", None) or []
        if not results:
            return "No results found for that query."
        lines = []
        for i, r in enumerate(results, 1):
            title = getattr(r, "title", None) or "No title"
            url = getattr(r, "url", None) or ""
            snippet = (getattr(r, "snippet", None) or getattr(r, "text", None) or "")[:500]
            lines.append(f"[{i}] {title}\nURL: {url}\n{snippet}")
        return "\n\n".join(lines)
    except Exception as e:
        return f"EXA search failed: {e!s}"


@tool
def exa_get_contents(
    urls: str,
    max_characters_per_url: Optional[int] = 15000,
) -> str:
    """
    Fetch full page content from a list of URLs using EXA.

    Use when you need full text from URLs returned by exa_web_search (or known links).
    Returns extracted main content (markdown-like). For SEC.gov or sites requiring
    JavaScript or login, use Unbrowse instead.

    Args:
        urls: Comma-separated list of URLs (e.g. "https://example.com/page1, https://example.com/page2").
        max_characters_per_url: Optional cap per URL to avoid huge responses (default 15000).

    Returns:
        Combined content from each URL, or error message if EXA is not configured or request failed.
    """
    exa = _get_exa_client()
    if exa is None:
        return (
            "EXA is not configured. Set EXA_API_KEY in .env. "
            "Use Unbrowse (unbrowse_resolve) for scraping specific sites."
        )
    url_list = [u.strip() for u in urls.split(",") if u.strip()]
    if not url_list:
        return "No URLs provided. Pass comma-separated URLs."
    try:
        raw = exa.get_contents(url_list, text=True)
        results = raw if isinstance(raw, list) else getattr(raw, "results", None) or [raw]
        if not results:
            return "No content retrieved for those URLs."
        parts = []
        for i, r in enumerate(results):
            url = getattr(r, "url", None) or f"Result {i+1}"
            text = (getattr(r, "text", None) or "")[: (max_characters_per_url or 15000)]
            parts.append(f"--- URL: {url} ---\n{text}")
        return "\n\n".join(parts)
    except Exception as e:
        return f"EXA get_contents failed: {e!s}"


def get_exa_tools():
    """Return EXA tools (exa_web_search, exa_get_contents) if EXA_API_KEY is set, else empty list."""
    if not os.getenv("EXA_API_KEY", "").strip():
        return []
    return [exa_web_search, exa_get_contents]
