from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.database import Base, SessionLocal, engine
from app.main import app
from app.services.workflow_engine import PlannerWorkflowService, WorkflowLaunch


client = TestClient(app)


class FakeWorkflowService(PlannerWorkflowService):
    async def start_job_workflow(self, job_id: str) -> WorkflowLaunch:
        return WorkflowLaunch(
            workflow_id=f"proof-of-browse-{job_id}",
            run_id="run-123",
            workflow_status="queued",
            current_activity="awaiting_worker",
            namespace="default",
            task_queue="proof-of-browse",
            temporal_ui_url="http://localhost:8088",
        )


def setup_function() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def test_run_job_queues_temporal_workflow(monkeypatch):
    monkeypatch.setattr("app.api.routes.PlannerWorkflowService", FakeWorkflowService)
    create_response = client.post(
        "/jobs",
        json={
            "goal": "Compare pricing",
            "target_urls": ["https://example.com/pricing"],
            "max_budget_usdc": 1,
        },
    )
    assert create_response.status_code == 200
    job_id = create_response.json()["job_id"]

    run_response = client.post(f"/jobs/{job_id}/run")
    assert run_response.status_code == 200
    payload = run_response.json()
    assert payload["status"] == "queued"
    assert payload["workflow"]["workflow_id"] == f"proof-of-browse-{job_id}"
    assert payload["workflow"]["run_id"] == "run-123"

    detail_response = client.get(f"/jobs/{job_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["workflow"]["workflow_status"] == "queued"
    assert any(event["event_type"] == "workflow_started" for event in detail["trace_events"])


def test_get_job_workflow_returns_persisted_status(monkeypatch):
    monkeypatch.setattr("app.api.routes.PlannerWorkflowService", FakeWorkflowService)
    create_response = client.post(
        "/jobs",
        json={
            "goal": "Compare pricing",
            "target_urls": ["https://example.com/pricing"],
            "max_budget_usdc": 1,
        },
    )
    job_id = create_response.json()["job_id"]
    client.post(f"/jobs/{job_id}/run")

    workflow_response = client.get(f"/jobs/{job_id}/workflow")
    assert workflow_response.status_code == 200
    payload = workflow_response.json()
    assert payload["job_id"] == job_id
    assert payload["workflow_status"] == "queued"
    assert payload["current_activity"] == "awaiting_worker"


def test_real_mode_requires_openai_and_postgres(monkeypatch):
    monkeypatch.setattr(settings, "app_mode", "real", raising=False)
    monkeypatch.setattr(settings, "planner_provider", "deterministic", raising=False)
    monkeypatch.setattr(settings, "payment_mode", "mock", raising=False)
    monkeypatch.setattr(settings, "settlement_mode", "app", raising=False)
    monkeypatch.setattr(settings, "postgres_url", "sqlite:///./proof-of-browse.db", raising=False)
    monkeypatch.setattr(settings, "openai_api_key", "", raising=False)
    try:
        settings.validate_runtime()
    except RuntimeError as exc:
        message = str(exc)
        assert "PLANNER_PROVIDER=openai" in message
        assert "OPENAI_API_KEY" in message
        assert "PAYMENT_MODE=real" in message
        assert "SETTLEMENT_MODE=alkahest" in message
        assert "POSTGRES_URL must point to Postgres" in message
    else:  # pragma: no cover
        raise AssertionError("Expected real mode validation to fail")
