from __future__ import annotations

from pydantic import BaseModel, Field


class QuoteRequest(BaseModel):
    task_id: str
    task_type: str
    target_url: str
    allowed_domain: str
    required_fields: list[str]


class QuoteResponse(BaseModel):
    worker_id: str
    task_id: str
    price_usdc: float
    eta_sec: int
    capabilities: list[str]


class BrowseRequest(BaseModel):
    task_id: str
    task_type: str
    target_url: str
    allowed_domain: str
    required_fields: list[str]


class EvidencePayload(BaseModel):
    screenshot_url: str
    html_hash: str
    excerpt: str


class BrowseResponse(BaseModel):
    task_id: str
    site: str
    final_url: str
    plan_name: str
    price_found: str
    timestamp: str
    evidence: EvidencePayload
    provider: str = "unbrowse"
    provider_run_id: str | None = None
    provider_status: str | None = None
    provider_metadata: dict[str, str] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str
    service: str
