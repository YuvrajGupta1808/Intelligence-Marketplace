"""
Unbrowse API-native browser automation tools for the deep research agent.

Integrates with the Unbrowse local server (http://localhost:6969 by default)
per https://github.com/unbrowse-ai/unbrowse and SKILL.md:
- Health check, intent resolve, skill search, execute by skill/endpoint,
  list skills, skill detail, feedback, and local skill registry.
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Optional

import requests
from langchain_core.tools import BaseTool, tool

from deep_research.config import PROJECT_ROOT

DEFAULT_UNBROWSE_URL = "http://localhost:6969"
UNBROWSE_CONFIG_PATH = Path.home() / ".unbrowse" / "config.json"
_UNBROWSE_REGISTRY_PATH = PROJECT_ROOT / "skills" / "unbrowse-company-data" / "registry.json"

logger = logging.getLogger(__name__)


def _get_base_url() -> str:
    return os.getenv("UNBROWSE_URL", DEFAULT_UNBROWSE_URL).rstrip("/")


def _get_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    api_key = os.getenv("UNBROWSE_API_KEY", "").strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        return headers
    if not UNBROWSE_CONFIG_PATH.exists():
        return headers
    try:
        with open(UNBROWSE_CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
        token = data.get("token") or data.get("accessToken")
        if token:
            headers["Authorization"] = f"Bearer {token}"
    except (json.JSONDecodeError, OSError, KeyError):
        pass
    return headers


def _request(
    method: str,
    path: str,
    json_body: Optional[dict] = None,
    timeout: int = 60,
) -> str:
    url = f"{_get_base_url()}{path}"
    try:
        if method == "GET":
            resp = requests.get(url, headers=_get_headers(), timeout=timeout)
        else:
            resp = requests.post(
                url, json=json_body or {}, headers=_get_headers(), timeout=timeout
            )
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.content:
            return "OK"
        data = resp.json()
        if isinstance(data, str):
            return data
        return json.dumps(data, indent=2)
    except requests.exceptions.ConnectionError:
        return json.dumps({
            "error": "Unbrowse service unreachable",
            "hint": "Start the service with `unbrowse` or `npx unbrowse setup`. Use other research tools (hybrid_search, live_finance_researcher) if Unbrowse is not needed.",
        })
    except requests.exceptions.Timeout:
        return json.dumps({"error": "Unbrowse request timed out"})
    except requests.exceptions.HTTPError as e:
        body = ""
        try:
            body = e.response.text
        except Exception:
            pass
        return json.dumps({
            "error": f"Unbrowse HTTP {e.response.status_code}",
            "detail": body or e.response.reason,
        })
    except Exception as e:
        return json.dumps({"error": f"Unbrowse request failed: {e!s}"})


@tool
def unbrowse_health() -> str:
    """
    Check if the Unbrowse local service is running (GET /health).

    Call this before relying on Unbrowse for web data. If it fails, use
    hybrid_search and live_finance_researcher instead, and tell the user
    Unbrowse is unavailable.
    """
    return _request("GET", "/health", timeout=5)


@tool
def unbrowse_resolve(
    intent: str,
    url: Optional[str] = None,
    context_url: Optional[str] = None,
    dry_run: bool = False,
) -> str:
    """
    Resolve a natural-language intent with Unbrowse (POST /v1/intent/resolve).

    Unbrowse searches the marketplace, captures the site if needed, then executes.
    Use for: fetching or extracting data from a specific website when SEC filings
    and Yahoo Finance are not sufficient (e.g. news site, broker page, data site).
    Unbrowse creates and stores skills on first resolve; other sub-agents reuse
    them when using the same Unbrowse URL. See docs/unbrowse.md.

    When no matching skill exists, Unbrowse requires context_url to trigger live
    capture (otherwise the server returns an error). Always pass context_url for
    SEC/EDGAR (e.g. the SEC company filings page URL for the ticker).

    Args:
        intent: Natural-language description (e.g. "get stock prices", "extract earnings from this page").
        url: Optional starting URL when you have a specific page.
        context_url: Required for first-time capture when no skill exists. Use the page URL to capture (e.g. SEC browse-edgar URL for the ticker).
        dry_run: If true, preview without executing (for mutations).

    Returns:
        JSON with result and often skill_id, endpoint_id, available_endpoints.
        Use unbrowse_execute with returned skill_id and endpoint_id for refined
        extraction (path, extract, limit). Submit feedback with unbrowse_feedback after presenting results.
    """
    params: dict = {}
    if url:
        params["url"] = url
    body: dict = {"intent": intent, "params": params}
    if context_url:
        body["context"] = {"url": context_url}
    if dry_run:
        body["dry_run"] = True
    return _request("POST", "/v1/intent/resolve", json_body=body)


@tool
def unbrowse_execute(
    skill_id: str,
    endpoint_id: str,
    path: Optional[str] = None,
    extract: Optional[str] = None,
    limit: Optional[int] = None,
    dry_run: bool = False,
    confirm_unsafe: bool = False,
    context_url: Optional[str] = None,
) -> str:
    """
    Execute a specific Unbrowse skill endpoint (POST /v1/skills/:id/execute).

    Use after unbrowse_resolve when you have skill_id and endpoint_id from the response.
    Use path and extract to get only the fields you need (avoids huge raw JSON).
    API: params.endpoint_id targets the endpoint; projection has path/extract/limit.

    Args:
        skill_id: Skill ID from resolve or list response.
        endpoint_id: Endpoint ID from resolve (e.g. available_endpoints) or skill detail.
        path: Optional path into the response (e.g. "data.events[]").
        extract: Optional comma-separated fields (e.g. "name,url,start_at").
        limit: Optional cap on array size.
        dry_run: Preview mutations without executing.
        confirm_unsafe: Required for non-GET mutations after dry_run.
        context_url: Optional URL context for the execution.

    Returns:
        JSON result or extraction. If response is large and you did not set path/extract,
        you may get extraction_hints; use those in a follow-up execute call.
    """
    params: dict = {"endpoint_id": endpoint_id}
    if context_url:
        params["context_url"] = context_url
    projection: dict = {}
    if path is not None:
        projection["path"] = path
    if extract is not None:
        projection["extract"] = extract
    if limit is not None:
        projection["limit"] = limit
    body: dict = {"params": params}
    if projection:
        body["projection"] = projection
    if dry_run:
        body["dry_run"] = True
    if confirm_unsafe:
        body["confirm_unsafe"] = True
    return _request("POST", f"/v1/skills/{skill_id}/execute", json_body=body)


@tool
def unbrowse_search(intent: str) -> str:
    """
    Search Unbrowse marketplace globally (POST /v1/search).

    Use to find existing skills by intent before or after resolve. Returns
    matching skills/endpoints; use skill_id and endpoint_id with unbrowse_execute.
    """
    return _request("POST", "/v1/search", json_body={"intent": intent})


@tool
def unbrowse_search_domain(intent: str, domain: str) -> str:
    """
    Search Unbrowse marketplace scoped to a domain (POST /v1/search/domain).

    Use when you care about a specific site (e.g. linkedin.com, lu.ma).
    """
    return _request(
        "POST", "/v1/search/domain", json_body={"intent": intent, "domain": domain}
    )


@tool
def unbrowse_list_skills() -> str:
    """
    List all Unbrowse marketplace skills (GET /v1/skills).

    Use to see what skills are already available before calling resolve.
    """
    return _request("GET", "/v1/skills")


@tool
def unbrowse_skill_detail(skill_id: str) -> str:
    """
    Get details for one Unbrowse skill (GET /v1/skills/:id).

    Use to inspect endpoints and metadata for a skill_id from resolve or list.
    """
    return _request("GET", f"/v1/skills/{skill_id}")


@tool
def unbrowse_feedback(
    skill_id: str,
    endpoint_id: str,
    rating: int,
    outcome: str = "success",
) -> str:
    """
    Submit feedback for an Unbrowse skill/endpoint (POST /v1/feedback).

    Call after presenting results to the user. Affects reliability scores.

    Args:
        skill_id: Skill ID that was used.
        endpoint_id: Endpoint ID that was used.
        rating: 5=right+fast, 4=right+slow, 3=incomplete, 2=wrong endpoint, 1=useless.
        outcome: Usually "success"; use "failure" if the result was wrong or broken.
    """
    return _request(
        "POST",
        "/v1/feedback",
        json_body={
            "skill_id": skill_id,
            "endpoint_id": endpoint_id,
            "rating": rating,
            "outcome": outcome,
        },
        timeout=10,
    )


@tool
def register_unbrowse_skill(
    skill_id: str,
    endpoint_id: str,
    intent: str,
    source_label: str,
) -> str:
    """
    Register an Unbrowse skill locally so other sub-agents can reuse it.

    Call after a successful unbrowse_resolve when you have skill_id and endpoint_id.
    The registry is stored under skills/unbrowse-company-data/registry.json.
    Other sub-agents can call get_unbrowse_registry() and then unbrowse_execute(skill_id, endpoint_id)
    without depending on the Unbrowse marketplace.

    Args:
        skill_id: Skill ID from the resolve response.
        endpoint_id: Endpoint ID from the resolve response (or available_endpoints).
        intent: The intent string that was used (e.g. "SEC.gov company filings for AAPL").
        source_label: Short label for the source (e.g. "SEC EDGAR", "sec-edgar").
    """
    entry = {
        "skill_id": skill_id,
        "endpoint_id": endpoint_id,
        "intent": intent,
        "source_label": source_label,
    }
    _UNBROWSE_REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        if _UNBROWSE_REGISTRY_PATH.exists():
            data = json.loads(_UNBROWSE_REGISTRY_PATH.read_text(encoding="utf-8"))
        else:
            data = []
        if not isinstance(data, list):
            data = []
        data.append(entry)
        _UNBROWSE_REGISTRY_PATH.write_text(
            json.dumps(data, indent=2), encoding="utf-8"
        )
        return json.dumps({
            "ok": True,
            "message": "Skill registered locally for sub-agents",
            "registry_path": str(_UNBROWSE_REGISTRY_PATH),
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to register skill: {e!s}"})


@tool
def get_unbrowse_registry() -> str:
    """
    Return the local Unbrowse skill registry (skills/unbrowse-company-data/registry.json).

    Use after loading the unbrowse-company-data skill. If the registry has entries for the
    source you need (e.g. SEC EDGAR), use the returned skill_id and endpoint_id with
    unbrowse_execute() so you do not need to call unbrowse_resolve.
    """
    if not _UNBROWSE_REGISTRY_PATH.exists():
        return json.dumps({"entries": [], "message": "No skills registered yet."})
    try:
        data = json.loads(_UNBROWSE_REGISTRY_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            data = []
        return json.dumps({"entries": data}, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to read registry: {e!s}"})


_UNBROWSE_TOOLS_LIST: List[BaseTool] = [
    unbrowse_health,
    unbrowse_resolve,
    unbrowse_execute,
    unbrowse_search,
    unbrowse_search_domain,
    unbrowse_list_skills,
    unbrowse_skill_detail,
    unbrowse_feedback,
    register_unbrowse_skill,
    get_unbrowse_registry,
]


def _unbrowse_health_check(timeout: int = 3) -> bool:
    """Return True if the Unbrowse service at UNBROWSE_URL is reachable."""
    url = f"{_get_base_url()}/health"
    try:
        resp = requests.get(url, headers=_get_headers(), timeout=timeout)
        return resp.status_code == 200
    except Exception:
        return False


def get_unbrowse_tools() -> List[BaseTool]:
    """
    Return Unbrowse tools. If the Unbrowse service is not running, tools are still
    returned so the graph loads and traces show tool use; each tool will return
    a clear error JSON when invoked (e.g. "Unbrowse service unreachable").
    """
    if _unbrowse_health_check():
        return _UNBROWSE_TOOLS_LIST
    logger.warning(
        "Unbrowse not reachable at %s; tools will return errors if called. "
        "Start with: unbrowse setup (or ./run.sh --unbrowse)",
        _get_base_url(),
    )
    return _UNBROWSE_TOOLS_LIST


UNBROWSE_TOOLS = _UNBROWSE_TOOLS_LIST
