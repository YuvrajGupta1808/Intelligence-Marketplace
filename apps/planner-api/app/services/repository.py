from __future__ import annotations

import json
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import utc_now_iso
from app.db.models import (
    ExecutionResultModel,
    JobModel,
    PlannerRunModel,
    QuoteModel,
    SettlementEventModel,
    TaskModel,
    TraceEventModel,
    VerificationResultModel,
    uuid_str,
)
from app.models.schemas import (
    ExecutionResultPayload,
    JobCreateRequest,
    JobWorkflowResponse,
    JobPayload,
    PlannerRunPayload,
    QuotePayload,
    SettlementEventPayload,
    TaskPayload,
    TraceEventPayload,
    VerificationResultPayload,
)


def _required_fields(task_type: str) -> list[str]:
    if task_type == "extract_pricing":
        return ["plan_name", "price_found"]
    return []


class PlannerRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_job(self, payload: JobCreateRequest) -> tuple[JobModel, list[TaskModel]]:
        job = JobModel(
            id=uuid_str(),
            goal=payload.goal,
            status="created",
            max_budget_usdc=payload.max_budget_usdc,
            created_at=utc_now_iso(),
        )
        self.db.add(job)
        self.db.flush()

        planner_run = PlannerRunModel(
            id=uuid_str(),
            job_id=job.id,
            planner_status="idle",
            current_step="awaiting_run",
            workflow_id=None,
            workflow_run_id=None,
            workflow_status="not_started",
            current_activity="awaiting_run",
            rationale_summary="Planner has not started yet.",
            selected_workers_json=json.dumps([]),
            decision_log_json=json.dumps([]),
            updated_at=utc_now_iso(),
        )
        self.db.add(planner_run)

        tasks: list[TaskModel] = []
        for url in payload.target_urls:
            domain = (urlparse(url).hostname or "").replace("www.", "")
            task = TaskModel(
                id=uuid_str(),
                job_id=job.id,
                task_type="extract_pricing",
                target_url=url,
                allowed_domain=domain,
                required_fields=json.dumps(_required_fields("extract_pricing")),
                status="pending",
                deadline_seconds=120,
            )
            self.db.add(task)
            tasks.append(task)

        self.db.commit()
        for task in tasks:
            self.db.refresh(task)
        self.db.refresh(job)
        return job, tasks

    def get_job(self, job_id: str) -> JobModel | None:
        return self.db.get(JobModel, job_id)

    def get_tasks(self, job_id: str) -> list[TaskModel]:
        return list(self.db.execute(select(TaskModel).where(TaskModel.job_id == job_id)).scalars())

    def get_task(self, task_id: str) -> TaskModel | None:
        return self.db.get(TaskModel, task_id)

    def get_planner_run(self, job_id: str) -> PlannerRunModel | None:
        return self.db.execute(select(PlannerRunModel).where(PlannerRunModel.job_id == job_id)).scalar_one_or_none()

    def set_job_status(self, job: JobModel, status: str) -> None:
        job.status = status
        self.db.commit()

    def set_task_status(self, task: TaskModel, status: str) -> None:
        task.status = status
        self.db.commit()

    def add_quote(self, payload: QuotePayload) -> None:
        existing = self.get_quote(payload.task_id)
        if existing is not None:
            return
        row = QuoteModel(
            id=uuid_str(),
            worker_id=payload.worker_id,
            task_id=payload.task_id,
            price_usdc=payload.price_usdc,
            eta_sec=payload.eta_sec,
            capabilities=json.dumps(payload.capabilities),
        )
        self.db.add(row)
        self.db.commit()

    def add_execution_result(self, payload: ExecutionResultPayload) -> None:
        if self.get_execution_result(payload.task_id) is not None:
            return
        self.db.add(ExecutionResultModel(id=uuid_str(), task_id=payload.task_id, payload_json=payload.model_dump_json()))
        self.db.commit()

    def add_verification_result(self, payload: VerificationResultPayload) -> None:
        if self.get_verification_result(payload.task_id) is not None:
            return
        self.db.add(VerificationResultModel(id=uuid_str(), task_id=payload.task_id, payload_json=payload.model_dump_json()))
        self.db.commit()

    def add_settlement_event(self, payload: SettlementEventPayload) -> None:
        if self.get_settlement_event(payload.task_id, payload.event_type) is not None:
            return
        self.db.add(
            SettlementEventModel(
                id=uuid_str(),
                task_id=payload.task_id,
                event_type=payload.event_type,
                amount_usdc=payload.amount_usdc,
                timestamp=payload.timestamp,
                metadata_json=json.dumps(payload.metadata),
            )
        )
        self.db.commit()

    def update_planner_run(
        self,
        planner_run: PlannerRunModel,
        *,
        planner_status: str | None = None,
        current_step: str | None = None,
        workflow_id: str | None = None,
        workflow_run_id: str | None = None,
        workflow_status: str | None = None,
        current_activity: str | None = None,
        rationale_summary: str | None = None,
        selected_workers: list[str] | None = None,
        decision_log: list[str] | None = None,
    ) -> None:
        if planner_status is not None:
            planner_run.planner_status = planner_status
        if current_step is not None:
            planner_run.current_step = current_step
        if workflow_id is not None:
            planner_run.workflow_id = workflow_id
        if workflow_run_id is not None:
            planner_run.workflow_run_id = workflow_run_id
        if workflow_status is not None:
            planner_run.workflow_status = workflow_status
        if current_activity is not None:
            planner_run.current_activity = current_activity
        if rationale_summary is not None:
            planner_run.rationale_summary = rationale_summary
        if selected_workers is not None:
            planner_run.selected_workers_json = json.dumps(selected_workers)
        if decision_log is not None:
            planner_run.decision_log_json = json.dumps(decision_log)
        planner_run.updated_at = utc_now_iso()
        self.db.commit()

    def add_trace_event(self, payload: TraceEventPayload) -> None:
        self.db.add(
            TraceEventModel(
                id=payload.id,
                planner_run_id=payload.planner_run_id,
                job_id=payload.job_id,
                task_id=payload.task_id,
                event_type=payload.event_type,
                title=payload.title,
                detail=payload.detail,
                metadata_json=json.dumps(payload.metadata),
                created_at=payload.created_at,
            )
        )
        self.db.commit()

    def list_quotes(self, task_ids: list[str]) -> list[QuotePayload]:
        if not task_ids:
            return []
        rows = list(self.db.execute(select(QuoteModel).where(QuoteModel.task_id.in_(task_ids))).scalars())
        return [
            QuotePayload(
                worker_id=row.worker_id,
                task_id=row.task_id,
                price_usdc=row.price_usdc,
                eta_sec=row.eta_sec,
                capabilities=json.loads(row.capabilities),
            )
            for row in rows
        ]

    def get_quote(self, task_id: str) -> QuotePayload | None:
        row = self.db.execute(select(QuoteModel).where(QuoteModel.task_id == task_id)).scalar_one_or_none()
        if row is None:
            return None
        return QuotePayload(
            worker_id=row.worker_id,
            task_id=row.task_id,
            price_usdc=row.price_usdc,
            eta_sec=row.eta_sec,
            capabilities=json.loads(row.capabilities),
        )

    def list_execution_results(self, task_ids: list[str]) -> list[ExecutionResultPayload]:
        rows = list(self.db.execute(select(ExecutionResultModel).where(ExecutionResultModel.task_id.in_(task_ids))).scalars())
        return [ExecutionResultPayload.model_validate_json(row.payload_json) for row in rows]

    def get_execution_result(self, task_id: str) -> ExecutionResultPayload | None:
        row = self.db.execute(select(ExecutionResultModel).where(ExecutionResultModel.task_id == task_id)).scalar_one_or_none()
        if row is None:
            return None
        return ExecutionResultPayload.model_validate_json(row.payload_json)

    def list_verification_results(self, task_ids: list[str]) -> list[VerificationResultPayload]:
        rows = list(self.db.execute(select(VerificationResultModel).where(VerificationResultModel.task_id.in_(task_ids))).scalars())
        return [VerificationResultPayload.model_validate_json(row.payload_json) for row in rows]

    def get_verification_result(self, task_id: str) -> VerificationResultPayload | None:
        row = self.db.execute(select(VerificationResultModel).where(VerificationResultModel.task_id == task_id)).scalar_one_or_none()
        if row is None:
            return None
        return VerificationResultPayload.model_validate_json(row.payload_json)

    def list_settlement_events(self, task_ids: list[str]) -> list[SettlementEventPayload]:
        rows = list(self.db.execute(select(SettlementEventModel).where(SettlementEventModel.task_id.in_(task_ids))).scalars())
        return [
            SettlementEventPayload(
                task_id=row.task_id,
                event_type=row.event_type,
                amount_usdc=row.amount_usdc,
                timestamp=row.timestamp,
                metadata=json.loads(row.metadata_json),
            )
            for row in rows
        ]

    def get_settlement_event(self, task_id: str, event_type: str) -> SettlementEventPayload | None:
        row = self.db.execute(
            select(SettlementEventModel).where(
                SettlementEventModel.task_id == task_id,
                SettlementEventModel.event_type == event_type,
            )
        ).scalar_one_or_none()
        if row is None:
            return None
        return SettlementEventPayload(
            task_id=row.task_id,
            event_type=row.event_type,
            amount_usdc=row.amount_usdc,
            timestamp=row.timestamp,
            metadata=json.loads(row.metadata_json),
        )

    def list_trace_events(self, planner_run_id: str) -> list[TraceEventPayload]:
        rows = list(
            self.db.execute(select(TraceEventModel).where(TraceEventModel.planner_run_id == planner_run_id)).scalars()
        )
        return [
            TraceEventPayload(
                id=row.id,
                planner_run_id=row.planner_run_id,
                job_id=row.job_id,
                task_id=row.task_id,
                event_type=row.event_type,
                title=row.title,
                detail=row.detail,
                metadata=json.loads(row.metadata_json),
                created_at=row.created_at,
            )
            for row in rows
        ]

    @staticmethod
    def job_payload(row: JobModel) -> JobPayload:
        return JobPayload(
            id=row.id,
            goal=row.goal,
            status=row.status,
            max_budget_usdc=row.max_budget_usdc,
            created_at=row.created_at,
        )

    @staticmethod
    def task_payload(row: TaskModel) -> TaskPayload:
        return TaskPayload(
            id=row.id,
            job_id=row.job_id,
            task_type=row.task_type,
            target_url=row.target_url,
            allowed_domain=row.allowed_domain,
            required_fields=json.loads(row.required_fields),
            status=row.status,
            deadline_seconds=row.deadline_seconds,
        )

    @staticmethod
    def planner_run_payload(row: PlannerRunModel) -> PlannerRunPayload:
        return PlannerRunPayload(
            id=row.id,
            job_id=row.job_id,
            planner_status=row.planner_status,
            current_step=row.current_step,
            workflow_id=row.workflow_id,
            workflow_run_id=row.workflow_run_id,
            workflow_status=row.workflow_status,
            current_activity=row.current_activity,
            rationale_summary=row.rationale_summary,
            selected_workers=json.loads(row.selected_workers_json),
            decision_log=json.loads(row.decision_log_json),
            updated_at=row.updated_at,
        )

    @staticmethod
    def workflow_payload(row: PlannerRunModel) -> JobWorkflowResponse:
        return JobWorkflowResponse(
            job_id=row.job_id,
            workflow_id=row.workflow_id,
            run_id=row.workflow_run_id,
            workflow_status=row.workflow_status,
            current_activity=row.current_activity,
            namespace=settings.temporal_namespace,
            task_queue=settings.temporal_task_queue,
            temporal_ui_url=settings.temporal_ui_url,
        )
