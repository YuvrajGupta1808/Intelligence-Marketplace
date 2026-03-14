from __future__ import annotations

from dataclasses import asdict, dataclass

from app.core.config import settings


@dataclass
class WorkflowLaunch:
    workflow_id: str
    run_id: str | None
    workflow_status: str
    current_activity: str
    namespace: str
    task_queue: str
    temporal_ui_url: str | None

    def as_payload(self) -> dict[str, str | None]:
        return asdict(self)


class PlannerWorkflowService:
    async def start_job_workflow(self, job_id: str) -> WorkflowLaunch:
        from temporalio.client import Client

        from app.temporal.workflows import ProofOfBrowseWorkflow, WorkflowInput

        client = await Client.connect(settings.temporal_target, namespace=settings.temporal_namespace)
        workflow_id = f"proof-of-browse-{job_id}"
        handle = await client.start_workflow(
            ProofOfBrowseWorkflow.run,
            WorkflowInput(job_id=job_id),
            id=workflow_id,
            task_queue=settings.temporal_task_queue,
        )
        return WorkflowLaunch(
            workflow_id=handle.id,
            run_id=getattr(handle, "first_execution_run_id", None) or getattr(handle, "result_run_id", None),
            workflow_status="queued",
            current_activity="awaiting_worker",
            namespace=settings.temporal_namespace,
            task_queue=settings.temporal_task_queue,
            temporal_ui_url=settings.temporal_ui_url,
        )
