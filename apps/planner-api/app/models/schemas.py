from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class JobCreateRequest(BaseModel):
    goal: str
    target_urls: list[str]
    max_budget_usdc: float = Field(gt=0)


class JobCreateResponse(BaseModel):
    job_id: str
    status: str
    task_ids: list[str]


class PlannerRunPayload(BaseModel):
    id: str
    job_id: str
    planner_status: str
    current_step: str
    workflow_id: str | None = None
    workflow_run_id: str | None = None
    workflow_status: str
    current_activity: str
    rationale_summary: str
    selected_workers: list[str]
    decision_log: list[str]
    updated_at: str


class WorkflowPayload(BaseModel):
    workflow_id: str | None = None
    run_id: str | None = None
    workflow_status: str
    current_activity: str
    namespace: str
    task_queue: str
    temporal_ui_url: str | None = None


class TraceEventPayload(BaseModel):
    id: str
    planner_run_id: str
    job_id: str
    task_id: str | None = None
    event_type: str
    title: str
    detail: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class TaskPayload(BaseModel):
    id: str
    job_id: str
    task_type: str
    target_url: str
    allowed_domain: str
    required_fields: list[str]
    status: str
    deadline_seconds: int = 120


class QuotePayload(BaseModel):
    worker_id: str
    task_id: str
    price_usdc: float
    eta_sec: int
    capabilities: list[str]


class ExecutionResultPayload(BaseModel):
    task_id: str
    site: str
    final_url: str
    plan_name: str
    price_found: str
    timestamp: str
    evidence: dict[str, Any]
    provider: str = "unbrowse"
    provider_run_id: str | None = None
    provider_status: str | None = None
    provider_metadata: dict[str, Any] = Field(default_factory=dict)


class VerificationResultPayload(BaseModel):
    task_id: str
    passed: bool
    score: float
    reasons: list[str]
    details: dict[str, Any] = Field(default_factory=dict)


class SettlementEventPayload(BaseModel):
    task_id: str
    event_type: str
    amount_usdc: float
    timestamp: str
    metadata: dict[str, Any]


class JobPayload(BaseModel):
    id: str
    goal: str
    status: str
    max_budget_usdc: float
    created_at: str


class JobDetailResponse(BaseModel):
    job: JobPayload
    planner_run: PlannerRunPayload
    workflow: WorkflowPayload
    trace_events: list[TraceEventPayload]
    tasks: list[TaskPayload]
    quotes: list[QuotePayload]
    execution_results: list[ExecutionResultPayload]
    verification_results: list[VerificationResultPayload]
    settlement_events: list[SettlementEventPayload]


class JobRunResponse(BaseModel):
    job_id: str
    status: str
    workflow: WorkflowPayload
    report: dict[str, Any] = Field(default_factory=dict)


class JobWorkflowResponse(WorkflowPayload):
    job_id: str
