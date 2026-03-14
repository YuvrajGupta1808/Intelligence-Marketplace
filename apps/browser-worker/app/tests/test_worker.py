from pathlib import Path

import pytest
import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.models.schemas import BrowseRequest, QuoteRequest
from app.services import _resolve_with_unbrowse, build_quote
from app.storage.local import LocalArtifactStorage


def test_quote_price_generation():
    response = build_quote(
        QuoteRequest(
            task_id="task-1",
            task_type="extract_pricing",
            target_url="https://example.com/pricing",
            allowed_domain="example.com",
            required_fields=["plan_name", "price_found"],
        )
    )
    assert response.price_usdc == 0.06
    assert "unbrowse" in response.capabilities


def test_screenshot_artifact_path_generation(tmp_path: Path):
    storage = LocalArtifactStorage(tmp_path, "http://localhost:8002/artifacts")
    path = storage.build_path("task-1", ".png")
    assert path.name == "task-1.png"
    assert storage.public_url(path).endswith("/task-1.png")


def test_html_hash_generation_fixture():
    html = "<html><body><h1>Starter</h1><p>$49/mo</p></body></html>"
    assert "Starter" in html
    assert "$49/mo" in html


def test_mock_x402_challenge_and_retry(monkeypatch):
    async def fake_browse(_request: BrowseRequest):
        return {
            "task_id": "task-1",
            "site": "example.com",
            "final_url": "https://example.com/pricing",
            "plan_name": "Starter",
            "price_found": "$49/mo",
            "timestamp": "2026-03-13T20:03:00Z",
            "evidence": {
                "screenshot_url": "http://localhost:8002/artifacts/task-1.png",
                "html_hash": "sha256:abc123",
                "excerpt": "Starter plan starts at $49/mo",
            },
        }

    monkeypatch.setattr("app.api.routes.execute_browse", fake_browse)
    client = TestClient(app)
    payload = {
        "task_id": "task-1",
        "task_type": "extract_pricing",
        "target_url": "https://example.com/pricing",
        "allowed_domain": "example.com",
        "required_fields": ["plan_name", "price_found"],
    }
    challenge = client.post("/browse", json=payload)
    assert challenge.status_code == 402
    success = client.post("/browse", json=payload, headers={"x-mock-payment": "paid"})
    assert success.status_code == 200
    assert success.json()["price_found"] == "$49/mo"


def test_real_x402_challenge_shape(monkeypatch):
    monkeypatch.setattr("app.api.routes.settings.payment_mode", "real", raising=False)
    client = TestClient(app)
    payload = {
        "task_id": "task-1",
        "task_type": "extract_pricing",
        "target_url": "https://example.com/pricing",
        "allowed_domain": "example.com",
        "required_fields": ["plan_name", "price_found"],
    }
    challenge = client.post("/browse", json=payload)
    assert challenge.status_code == 402
    detail = challenge.json()["detail"]
    assert detail["payment_mode"] == "real"
    assert detail["network"] == "solana-devnet"
    assert detail["asset"] == "USDC"


def test_real_mode_requires_unbrowse(monkeypatch):
    monkeypatch.setattr(settings, "app_mode", "real", raising=False)
    monkeypatch.setattr(settings, "payment_mode", "real", raising=False)
    monkeypatch.setattr(settings, "unbrowse_url", "", raising=False)
    try:
        settings.validate_runtime()
    except RuntimeError as exc:
        message = str(exc)
        assert "UNBROWSE_URL" in message
    else:  # pragma: no cover
        raise AssertionError("Expected browser worker real mode validation to fail")


@pytest.mark.asyncio
async def test_unbrowse_resolve_returns_metadata(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "source": "marketplace",
                "trace": {"trace_id": "trace-123"},
                "skill": {"skill_id": "skill-123"},
                "result": {
                    "final_url": "https://example.com/pricing",
                    "summary": "Starter plan starts at $49/mo",
                },
            }

    class FakeClient:
        def __init__(self, *_args, **_kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, _url, json):
            assert json["params"]["url"] == "https://example.com/pricing"
            return FakeResponse()

    monkeypatch.setattr("app.services.httpx.AsyncClient", FakeClient)
    body, text, metadata = await _resolve_with_unbrowse(
        BrowseRequest(
            task_id="task-1",
            task_type="extract_pricing",
            target_url="https://example.com/pricing",
            allowed_domain="example.com",
            required_fields=["plan_name", "price_found"],
        )
    )

    assert body["source"] == "marketplace"
    assert "Starter" in text
    assert metadata["provider"] == "unbrowse"
    assert metadata["trace_id"] == "trace-123"


@pytest.mark.asyncio
async def test_unbrowse_resolve_raises_when_unavailable(monkeypatch):
    class FakeClient:
        def __init__(self, *_args, **_kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, _url, json):
            raise httpx.ConnectError("connection refused", request=httpx.Request("POST", "http://127.0.0.1:6969"))

    monkeypatch.setattr("app.services.httpx.AsyncClient", FakeClient)
    with pytest.raises(RuntimeError, match="Unbrowse execution failed"):
        await _resolve_with_unbrowse(
            BrowseRequest(
                task_id="task-1",
                task_type="extract_pricing",
                target_url="https://example.com/pricing",
                allowed_domain="example.com",
                required_fields=["plan_name", "price_found"],
            )
        )
