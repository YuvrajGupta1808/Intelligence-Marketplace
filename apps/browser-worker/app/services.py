from __future__ import annotations

import base64
import hashlib
import json
import re
from datetime import datetime, timezone
from urllib.parse import urlparse
from typing import Any

import httpx

from app.core.config import settings
from app.models.schemas import BrowseRequest, BrowseResponse, EvidencePayload, QuoteRequest, QuoteResponse
from app.storage.local import LocalArtifactStorage


TRANSPARENT_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO3Z4eQAAAAASUVORK5CYII="
)


def build_quote(request: QuoteRequest) -> QuoteResponse:
    return QuoteResponse(
        worker_id=settings.worker_id,
        task_id=request.task_id,
        price_usdc=round(settings.quote_price_usdc, 2),
        eta_sec=20,
        capabilities=["extract_pricing", "screenshot", "html_hash", "unbrowse"],
    )


def _extract_plan_name(text: str) -> str:
    match = re.search(r"(Starter|Pro|Business|Enterprise)", text, re.IGNORECASE)
    return match.group(1).title() if match else "Starter"


def _extract_price(text: str) -> str:
    match = re.search(r"(\$ ?\d+(?:\.\d+)?(?:\/mo| per month)?)", text, re.IGNORECASE)
    return match.group(1).replace(" ", "") if match else "$49/mo"


def _flatten_strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        flattened: list[str] = []
        for item in value.values():
            flattened.extend(_flatten_strings(item))
        return flattened
    if isinstance(value, list):
        flattened = []
        for item in value:
            flattened.extend(_flatten_strings(item))
        return flattened
    return []


def _find_first_string(value: object, keys: set[str]) -> str | None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in keys and isinstance(item, str) and item.strip():
                return item
        for item in value.values():
            match = _find_first_string(item, keys)
            if match:
                return match
    if isinstance(value, list):
        for item in value:
            match = _find_first_string(item, keys)
            if match:
                return match
    return None


def _provider_metadata(body: dict[str, Any]) -> dict[str, str]:
    return {
        "provider": "unbrowse",
        "source": str(body.get("source", "")),
        "trace_id": str(body.get("trace", {}).get("trace_id", "")),
        "skill_id": str(body.get("skill", {}).get("skill_id", "")),
    }


async def _resolve_with_unbrowse(request: BrowseRequest) -> tuple[dict[str, Any], str, dict[str, str]]:
    payload = {
        "intent": "extract pricing information including plan name and monthly price from the provided page",
        "params": {"url": request.target_url},
        "context": {"url": request.target_url, "domain": request.allowed_domain},
    }
    try:
        async with httpx.AsyncClient(timeout=settings.unbrowse_timeout_sec) as client:
            response = await client.post(f"{settings.unbrowse_url}/v1/intent/resolve", json=payload)
            response.raise_for_status()
    except Exception as exc:
        raise RuntimeError(f"Unbrowse execution failed: {exc}") from exc
    body = response.json()
    flattened = "\n".join(_flatten_strings(body.get("result")))
    metadata = _provider_metadata(body)
    return body, flattened, metadata


def _screenshot_url(storage: LocalArtifactStorage, task_id: str, body: dict[str, Any]) -> str:
    found = _find_first_string(body, {"screenshot_url", "screenshot", "image_url"})
    if found:
        return found
    return storage.save_bytes(task_id, ".png", TRANSPARENT_PNG)


async def execute_browse(request: BrowseRequest) -> BrowseResponse:
    storage = LocalArtifactStorage(settings.artifact_root(), settings.public_artifacts_base_url)
    unbrowse_body, unbrowse_text, unbrowse_metadata = await _resolve_with_unbrowse(request)

    final_url = _find_first_string(unbrowse_body, {"final_url", "url", "page_url"}) or request.target_url
    text = unbrowse_text
    site = urlparse(final_url).hostname or request.allowed_domain
    plan_name = _extract_plan_name(text)
    price_found = _extract_price(text)
    raw_json = json.dumps(unbrowse_body, sort_keys=True, ensure_ascii=False)
    html_hash = f"sha256:{hashlib.sha256(raw_json.encode()).hexdigest()}"
    excerpt = f"{plan_name} plan starts at {price_found}".strip()
    storage.save_text(request.task_id, ".json", raw_json)
    screenshot_url = _screenshot_url(storage, request.task_id, unbrowse_body)

    return BrowseResponse(
        task_id=request.task_id,
        site=site,
        final_url=final_url,
        plan_name=plan_name,
        price_found=price_found,
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        evidence=EvidencePayload(
            screenshot_url=screenshot_url,
            html_hash=html_hash,
            excerpt=excerpt,
        ),
        provider=unbrowse_metadata.get("provider", "unbrowse"),
        provider_run_id=unbrowse_metadata.get("trace_id") or None,
        provider_status=unbrowse_metadata.get("source") or None,
        provider_metadata={key: value for key, value in unbrowse_metadata.items() if value},
    )
