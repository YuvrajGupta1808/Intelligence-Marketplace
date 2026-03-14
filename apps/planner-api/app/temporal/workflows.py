from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any
from temporalio.common import RetryPolicy


@dataclass
class WorkflowInput:
    job_id: str


def _imports():
    from temporalio import workflow

    with workflow.unsafe.imports_passed_through():
        from app.temporal import activities

    return workflow, activities


workflow, activities = _imports()


@workflow.defn
class ProofOfBrowseWorkflow:
    @workflow.run
    async def run(self, payload: WorkflowInput) -> dict[str, Any]:
        plan = await workflow.execute_activity(
            activities.generate_plan,
            payload.job_id,
            start_to_close_timeout=timedelta(seconds=60),
        )
        report_tasks: list[dict[str, Any]] = []
        for task_id in plan.execution_order:
            quote = await workflow.execute_activity(
                activities.request_quote,
                args=[payload.job_id, task_id],
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            funded = await workflow.execute_activity(
                activities.fund_escrow,
                args=[payload.job_id, task_id, quote],
                start_to_close_timeout=timedelta(seconds=60),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            execution = await workflow.execute_activity(
                activities.pay_and_browse,
                args=[payload.job_id, task_id],
                start_to_close_timeout=timedelta(seconds=120),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            verification = await workflow.execute_activity(
                activities.verify_result,
                args=[payload.job_id, task_id, execution],
                start_to_close_timeout=timedelta(seconds=60),
            )
            settlement = await workflow.execute_activity(
                activities.settle_task,
                args=[payload.job_id, task_id, quote, verification, execution, funded],
                start_to_close_timeout=timedelta(seconds=120),
                retry_policy=RetryPolicy(maximum_attempts=3),
            )
            report_tasks.append(
                {
                    "task_id": task_id,
                    "planner_provider": plan.provider,
                    "quote": quote,
                    "result": execution,
                    "verification": verification,
                    "settlement": settlement["event_type"],
                }
            )
        final_result = await workflow.execute_activity(
            activities.finalize_job,
            payload.job_id,
            start_to_close_timeout=timedelta(seconds=30),
        )
        return {"summary": report_tasks, "tasks": report_tasks, "released": final_result["released"]}
