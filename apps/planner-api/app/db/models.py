from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


def uuid_str() -> str:
    return str(uuid.uuid4())


class JobModel(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    max_budget_usdc: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)


class PlannerRunModel(Base):
    __tablename__ = "planner_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), nullable=False, unique=True)
    planner_status: Mapped[str] = mapped_column(String(64), nullable=False)
    current_step: Mapped[str] = mapped_column(String(128), nullable=False)
    rationale_summary: Mapped[str] = mapped_column(Text, nullable=False)
    selected_workers_json: Mapped[str] = mapped_column(Text, nullable=False)
    decision_log_json: Mapped[str] = mapped_column(Text, nullable=False)
    workflow_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    workflow_run_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    workflow_status: Mapped[str] = mapped_column(String(64), nullable=False, default="not_started")
    current_activity: Mapped[str] = mapped_column(String(128), nullable=False, default="awaiting_run")
    updated_at: Mapped[str] = mapped_column(String(64), nullable=False)


class TaskModel(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), nullable=False)
    task_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_url: Mapped[str] = mapped_column(Text, nullable=False)
    allowed_domain: Mapped[str] = mapped_column(String(255), nullable=False)
    required_fields: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    deadline_seconds: Mapped[int] = mapped_column(nullable=False, default=120)


class QuoteModel(Base):
    __tablename__ = "quotes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    worker_id: Mapped[str] = mapped_column(String(64), nullable=False)
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("tasks.id"), nullable=False)
    price_usdc: Mapped[float] = mapped_column(Float, nullable=False)
    eta_sec: Mapped[int] = mapped_column(nullable=False)
    capabilities: Mapped[str] = mapped_column(Text, nullable=False)


class ExecutionResultModel(Base):
    __tablename__ = "execution_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("tasks.id"), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)


class VerificationResultModel(Base):
    __tablename__ = "verification_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("tasks.id"), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)


class SettlementEventModel(Base):
    __tablename__ = "settlement_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    task_id: Mapped[str] = mapped_column(String(36), ForeignKey("tasks.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    amount_usdc: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False)


class TraceEventModel(Base):
    __tablename__ = "trace_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    planner_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("planner_runs.id"), nullable=False)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), nullable=False)
    task_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tasks.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
