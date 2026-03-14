from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlparse

from app.models.schemas import VerifyRequest, VerificationResultPayload


PASS_REASONS = {
    "screenshot_present",
    "domain_match",
    "required_fields_present",
    "excerpt_match",
    "hash_present",
    "timestamp_present",
    "deadline_ok",
}


def _parse_timestamp(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def verify(request: VerifyRequest) -> VerificationResultPayload:
    reasons: list[str] = []
    details: dict[str, str] = {}
    result = request.execution_result
    task = request.task
    excerpt = result.evidence.excerpt.lower()

    if result.evidence.screenshot_url:
        reasons.append("screenshot_present")
    else:
        reasons.append("missing_screenshot")

    final_domain = (urlparse(result.final_url).hostname or "").lower()
    if final_domain == task.allowed_domain.lower():
        reasons.append("domain_match")
    else:
        reasons.append("domain_mismatch")
        details["allowed_domain"] = task.allowed_domain
        details["final_url"] = result.final_url

    extracted = result.extracted_values()
    missing_fields = [field for field in task.required_fields if not extracted.get(field)]
    if missing_fields:
        reasons.append("missing_required_field")
        details["missing_required_field"] = ",".join(missing_fields)
    else:
        reasons.append("required_fields_present")

    excerpt_supported = all(value.lower() in excerpt for value in extracted.values())
    if extracted and excerpt_supported:
        reasons.append("excerpt_match")
    else:
        reasons.append("excerpt_not_supportive")

    if result.evidence.html_hash:
        reasons.append("hash_present")
    else:
        reasons.append("missing_html_hash")

    timestamp = _parse_timestamp(result.timestamp)
    if timestamp:
        reasons.append("timestamp_present")
    else:
        reasons.append("missing_timestamp")

    if timestamp:
        age_seconds = (datetime.now(timezone.utc) - timestamp.astimezone(timezone.utc)).total_seconds()
        if age_seconds <= task.deadline_seconds:
            reasons.append("deadline_ok")
        else:
            reasons.append("deadline_exceeded")
            details["deadline_seconds"] = str(task.deadline_seconds)

    failures = [reason for reason in reasons if reason not in PASS_REASONS]
    score = max(0.0, 1.0 - (len(failures) * 0.17))

    return VerificationResultPayload(
        task_id=task.id,
        passed=not failures,
        score=round(score, 2),
        reasons=reasons,
        details=details,
    )

