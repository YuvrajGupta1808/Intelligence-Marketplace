from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.time import utc_now_iso
from app.db.database import get_db
from app.db.models import uuid_str
from app.models.schemas import (
    HealthResponse,
    JobCreateRequest,
    JobCreateResponse,
    JobDetailResponse,
    JobRunResponse,
    JobWorkflowResponse,
    TraceEventPayload,
)
from app.services.orchestrator import PlannerOrchestrator
from app.services.repository import PlannerRepository
from app.services.workflow_engine import PlannerWorkflowService


router = APIRouter()


@router.post("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="planner-api")


@router.post("/jobs", response_model=JobCreateResponse)
def create_job(payload: JobCreateRequest, db: Session = Depends(get_db)) -> JobCreateResponse:
    repo = PlannerRepository(db)
    job, tasks = repo.create_job(payload)
    return JobCreateResponse(job_id=job.id, status=job.status, task_ids=[task.id for task in tasks])


@router.get("/jobs/{job_id}", response_model=JobDetailResponse)
def get_job(job_id: str, db: Session = Depends(get_db)) -> JobDetailResponse:
    orchestrator = PlannerOrchestrator(db)
    try:
        return orchestrator.get_job_detail(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/jobs/{job_id}/run", response_model=JobRunResponse)
async def run_job(job_id: str, db: Session = Depends(get_db)) -> JobRunResponse:
    repo = PlannerRepository(db)
    job = repo.get_job(job_id)
    planner_run = repo.get_planner_run(job_id)
    if job is None or planner_run is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if planner_run.workflow_id and planner_run.workflow_status in {"queued", "running"}:
        return JobRunResponse(job_id=job.id, status=job.status, workflow=repo.workflow_payload(planner_run))
    workflow_service = PlannerWorkflowService()
    try:
        launch = await workflow_service.start_job_workflow(job_id)
    except Exception as exc:  # pragma: no cover - runtime integration failure
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    repo.set_job_status(job, "queued")
    repo.update_planner_run(
        planner_run,
        planner_status="queued",
        current_step="workflow_started",
        workflow_id=launch.workflow_id,
        workflow_run_id=launch.run_id,
        workflow_status=launch.workflow_status,
        current_activity=launch.current_activity,
    )
    repo.add_trace_event(
        TraceEventPayload(
            id=uuid_str(),
            planner_run_id=planner_run.id,
            job_id=job.id,
            task_id=None,
            event_type="workflow_started",
            title="Temporal workflow started",
            detail=f"Queued Temporal workflow {launch.workflow_id} on {launch.task_queue}.",
            metadata=launch.as_payload(),
            created_at=utc_now_iso(),
        )
    )
    refreshed_planner_run = repo.get_planner_run(job_id)
    if refreshed_planner_run is None:
        raise HTTPException(status_code=404, detail="Planner run not found")
    return JobRunResponse(job_id=job.id, status=job.status, workflow=repo.workflow_payload(refreshed_planner_run))


@router.get("/jobs/{job_id}/workflow", response_model=JobWorkflowResponse)
def get_job_workflow(job_id: str, db: Session = Depends(get_db)) -> JobWorkflowResponse:
    repo = PlannerRepository(db)
    planner_run = repo.get_planner_run(job_id)
    if planner_run is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return repo.workflow_payload(planner_run)
