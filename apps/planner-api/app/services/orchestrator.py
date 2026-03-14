from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.schemas import JobDetailResponse
from app.services.repository import PlannerRepository


class PlannerOrchestrator:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = PlannerRepository(db)

    def get_job_detail(self, job_id: str) -> JobDetailResponse:
        job = self.repo.get_job(job_id)
        if job is None:
            raise ValueError("Job not found")
        planner_run = self.repo.get_planner_run(job_id)
        if planner_run is None:
            raise ValueError("Planner run not found")
        tasks = self.repo.get_tasks(job_id)
        task_ids = [task.id for task in tasks]
        return JobDetailResponse(
            job=self.repo.job_payload(job),
            planner_run=self.repo.planner_run_payload(planner_run),
            workflow=self.repo.workflow_payload(planner_run),
            trace_events=self.repo.list_trace_events(planner_run.id),
            tasks=[self.repo.task_payload(task) for task in tasks],
            quotes=self.repo.list_quotes(task_ids),
            execution_results=self.repo.list_execution_results(task_ids),
            verification_results=self.repo.list_verification_results(task_ids),
            settlement_events=self.repo.list_settlement_events(task_ids),
        )
