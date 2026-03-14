from datetime import datetime, timedelta, timezone

from app.models.schemas import EvidencePayload, ExecutionResultPayload, TaskPayload, VerifyRequest
from app.rules.engine import verify


def make_request(**overrides):
    timestamp = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
    task = TaskPayload(
        id="task-1",
        job_id="job-1",
        task_type="extract_pricing",
        target_url="https://example.com/pricing",
        allowed_domain="example.com",
        required_fields=["plan_name", "price_found"],
        status="completed",
    )
    result = ExecutionResultPayload(
        task_id="task-1",
        site="example.com",
        final_url="https://example.com/pricing",
        plan_name="Starter",
        price_found="$49/mo",
        timestamp=timestamp,
        evidence=EvidencePayload(
            screenshot_url="http://localhost:8002/artifacts/task-1.png",
            html_hash="sha256:abc123",
            excerpt="Starter plan starts at $49/mo on the pricing page.",
        ),
    )
    payload = VerifyRequest(task=task, execution_result=result)
    for key, value in overrides.items():
        if key.startswith("task__"):
            setattr(payload.task, key.removeprefix("task__"), value)
        elif key.startswith("result__"):
            setattr(payload.execution_result, key.removeprefix("result__"), value)
        elif key.startswith("evidence__"):
            setattr(payload.execution_result.evidence, key.removeprefix("evidence__"), value)
    return payload


def test_verify_passes():
    outcome = verify(make_request())
    assert outcome.passed is True
    assert "domain_match" in outcome.reasons


def test_verify_domain_mismatch():
    outcome = verify(make_request(result__final_url="https://other.com/pricing"))
    assert outcome.passed is False
    assert "domain_mismatch" in outcome.reasons


def test_verify_missing_screenshot():
    outcome = verify(make_request(evidence__screenshot_url=""))
    assert outcome.passed is False
    assert "missing_screenshot" in outcome.reasons


def test_verify_missing_required_field():
    outcome = verify(make_request(result__price_found=None))
    assert outcome.passed is False
    assert "missing_required_field" in outcome.reasons


def test_verify_deadline_exceeded():
    old_timestamp = (datetime.now(timezone.utc) - timedelta(seconds=500)).isoformat()
    outcome = verify(make_request(result__timestamp=old_timestamp))
    assert outcome.passed is False
    assert "deadline_exceeded" in outcome.reasons

