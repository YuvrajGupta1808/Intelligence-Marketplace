"""Deep finance research tool that calls the deep-research agent API."""

import json
import os
from typing import Any

import requests
from langchain_core.tools import tool


def _get_base_url() -> str:
    """Return the base URL for the deep-research API."""
    # Default matches local uvicorn run in deep-research:
    # uv run uvicorn deep_research.api:app --reload --port 8000
    return os.getenv("DEEP_RESEARCH_URL", "http://localhost:8000").rstrip("/")


@tool
def deep_research_stock(query: str) -> str:
    """Run the Deep Finance Research agent for detailed stock or company analysis.

    Use this when the user asks for equity or stock analysis, investment theses, risks, valuation,
    or other deep fundamental research about a public company or financial asset.

    Input should be a concise description including any tickers (e.g. "AAPL long-term investment
    thesis and key risks", "Compare NVDA vs AMD as investments over the next 3 years")."""
    base_url = _get_base_url()
    url = f"{base_url}/research_report"
    try:
        resp = requests.post(
            url,
            json={"query": query},
            timeout=float(os.getenv("DEEP_RESEARCH_TIMEOUT_SECONDS", "900")),
        )
    except Exception as e:  # pragma: no cover - network failure path
        return (
            f"[deep_research_stock error] Failed to reach deep-research API at {url}: {e}. "
            "If this was a timeout, try increasing DEEP_RESEARCH_TIMEOUT_SECONDS (seconds) in your environment."
        )

    if resp.status_code != 200:
        # Try to surface any error message from the API.
        try:
            data: Any = resp.json()
            detail = data.get("detail") or data
        except Exception:
            detail = resp.text
        return f"[deep_research_stock error] API returned {resp.status_code}: {detail}"

    try:
        data: Any = resp.json()
    except Exception:
        return "[deep_research_stock error] Response from API was not valid JSON."

    report = data.get("report")
    if not report:
        return f"[deep_research_stock warning] API response did not include a 'report' field: {data}"

    # Some models may return a function-call style JSON blob instead of the
    # final markdown report (e.g. a write_todos plan). When that happens,
    # try to parse and turn it into a readable research plan instead of raw JSON.
    try:
        parsed = json.loads(report)
    except Exception:
        return report

    if isinstance(parsed, dict) and parsed.get("type") == "function":
        name = parsed.get("name") or "task"
        params = parsed.get("parameters") or {}
        todos_raw = params.get("todos")
        todos: list[dict[str, Any]] = []
        if isinstance(todos_raw, str):
            try:
                todos = json.loads(todos_raw)
            except Exception:
                todos = []
        elif isinstance(todos_raw, list):
            todos = todos_raw

        if todos:
            lines = [f"Deep research {name} plan:"]
            for i, todo in enumerate(todos, 1):
                content = str(todo.get("content") or "").strip()
                status = str(todo.get("status") or "pending")
                if content:
                    lines.append(f"{i}. {content} (status: {status})")
            if len(lines) > 1:
                return "\n".join(lines)

    # Fallback: return whatever the API gave us.
    return report


def get_deep_research_tool():
    """Return the deep finance research tool."""
    return deep_research_stock

