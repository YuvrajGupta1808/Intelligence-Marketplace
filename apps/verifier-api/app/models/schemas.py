from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TaskPayload(BaseModel):
    id: str
    job_id: str
    task_type: str
    target_url: str
    allowed_domain: str
    required_fields: list[str]
    status: str
    deadline_seconds: int = 120


class EvidencePayload(BaseModel):
    screenshot_url: str
    html_hash: str
    excerpt: str


class ExecutionResultPayload(BaseModel):
    task_id: str
    site: str
    final_url: str
    plan_name: str | None = None
    price_found: str | None = None
    timestamp: str
    evidence: EvidencePayload
    provider: str = "unbrowse"
    provider_run_id: str | None = None
    provider_status: str | None = None
    provider_metadata: dict[str, Any] = Field(default_factory=dict)

    def extracted_values(self) -> dict[str, str]:
        values: dict[str, str] = {}
        if self.plan_name:
            values["plan_name"] = self.plan_name
        if self.price_found:
            values["price_found"] = self.price_found
        return values


class VerifyRequest(BaseModel):
    task: TaskPayload
    execution_result: ExecutionResultPayload


class VerificationResultPayload(BaseModel):
    task_id: str
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    reasons: list[str]
    details: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str
    service: str
