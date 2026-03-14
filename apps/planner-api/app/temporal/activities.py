from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from temporalio import activity

from app.core.config import settings
from app.core.time import utc_now_iso
from app.db.database import SessionLocal
from app.models.schemas import ExecutionResultPayload, QuotePayload, SettlementEventPayload, VerificationResultPayload
from app.services.agent_runtime import PlannerAgentRuntime
from app.services.clients import HttpSettlementClient, HttpVerifierClient, HttpWorkerClient, MockPaymentClient, RealPaymentClient
from app.services.planner import PlannerService
from app.services.repository import PlannerRepository
from app.services.settlement import build_settlement_adapter


@dataclass
class PlanData:
    provider: str
    execution_order: list[str]
    selected_workers: list[str]
    rationale_summary: str
    settlement_policy: str


def _temporal_metadata(activity_type: str) -> dict[str, object]:
    info = activity.info()
    return {
        "activity_type": activity_type,
        "workflow_id": info.workflow_id,
        "workflow_run_id": info.workflow_run_id,
        "activity_attempt": info.attempt,
        "workflow_engine": "temporal",
        "task_queue": settings.temporal_task_queue,
    }


def _clients() -> tuple[HttpWorkerClient, HttpVerifierClient, HttpSettlementClient]:
    payment = RealPaymentClient() if settings.payment_mode == "real" else MockPaymentClient()
    return HttpWorkerClient(payment_client=payment), HttpVerifierClient(), HttpSettlementClient()


@activity.defn
async def generate_plan(job_id: str) -> PlanData:
    with SessionLocal() as db:
        repo = PlannerRepository(db)
        job = repo.get_job(job_id)
        planner_run = repo.get_planner_run(job_id)
        if job is None or planner_run is None:
            raise ValueError("Job not found")
        tasks = repo.get_tasks(job_id)
        task_payloads = [repo.task_payload(task) for task in tasks]
        repo.set_job_status(job, "planning")
        repo.update_planner_run(
            planner_run,
            planner_status="planning",
            workflow_status="running",
            current_activity="generate_plan",
        )
        runtime = PlannerAgentRuntime(repo, planner_run)
        plan = await PlannerService().generate_plan(job.goal, task_payloads, job.max_budget_usdc)
        runtime.bootstrap(job.goal, task_payloads, plan, metadata=_temporal_metadata("generate_plan"))
        return PlanData(
            provider=plan.provider,
            execution_order=plan.execution_order,
            selected_workers=plan.selected_workers,
            rationale_summary=plan.rationale_summary,
            settlement_policy=plan.settlement_policy,
        )


@activity.defn
async def request_quote(job_id: str, task_id: str) -> dict[str, Any]:
    worker_client, _, _ = _clients()
    with SessionLocal() as db:
        repo = PlannerRepository(db)
        job = repo.get_job(job_id)
        planner_run = repo.get_planner_run(job_id)
        task_row = repo.get_task(task_id)
        if job is None or planner_run is None or task_row is None:
            raise ValueError("Task not found")
        task = repo.task_payload(task_row)
        runtime = PlannerAgentRuntime(repo, planner_run)
        runtime.tool_call(
            task,
            "quote_worker",
            f"Requesting deterministic worker quote for {task.allowed_domain}.",
            metadata=_temporal_metadata("request_quote"),
        )
        quote = repo.get_quote(task_id)
        if quote is None:
            quote = await worker_client.quote(task)
            repo.add_quote(quote)
        runtime.record_quote(task, quote, metadata=_temporal_metadata("request_quote"))
        repo.set_task_status(task_row, "quoted")
        repo.set_job_status(job, "quoted")
        return quote.model_dump()


@activity.defn
async def fund_escrow(job_id: str, task_id: str, quote_data: dict[str, Any]) -> dict[str, Any]:
    _, _, settlement_client = _clients()
    settlement = build_settlement_adapter()
    quote = QuotePayload.model_validate(quote_data)
    with SessionLocal() as db:
        repo = PlannerRepository(db)
        job = repo.get_job(job_id)
        planner_run = repo.get_planner_run(job_id)
        task_row = repo.get_task(task_id)
        if job is None or planner_run is None or task_row is None:
            raise ValueError("Task not found")
        existing = repo.get_settlement_event(task_id, "funded")
        if existing is not None:
            return existing.metadata
        task = repo.task_payload(task_row)
        runtime = PlannerAgentRuntime(repo, planner_run)
        runtime.tool_call(
            task,
            "fund_escrow",
            f"Funding escrow for {task.allowed_domain} before paid execution.",
            metadata=_temporal_metadata("fund_escrow"),
        )
        funded_event = settlement.funded_event(task, quote)
        if settings.settlement_mode == "alkahest":
            funded_event.metadata = await settlement_client.fund(task, quote)
        repo.add_settlement_event(funded_event)
        repo.set_task_status(task_row, "funded")
        repo.set_job_status(job, "funded")
        return funded_event.metadata


@activity.defn
async def pay_and_browse(job_id: str, task_id: str) -> dict[str, Any]:
    worker_client, _, _ = _clients()
    with SessionLocal() as db:
        repo = PlannerRepository(db)
        job = repo.get_job(job_id)
        planner_run = repo.get_planner_run(job_id)
        task_row = repo.get_task(task_id)
        if job is None or planner_run is None or task_row is None:
            raise ValueError("Task not found")
        task = repo.task_payload(task_row)
        runtime = PlannerAgentRuntime(repo, planner_run)
        runtime.tool_call(
            task,
            "request_browse",
            f"Calling paid browse tool for {task.target_url}.",
            metadata=_temporal_metadata("pay_and_browse"),
        )
        existing = repo.get_execution_result(task_id)
        if existing is not None:
            return existing.model_dump()
        repo.set_task_status(task_row, "running")
        repo.set_job_status(job, "payment_sent")
        paid_execution = await worker_client.browse(task)
        runtime.record_payment_challenge(
            task,
            paid_execution.payment_metadata,
            metadata=_temporal_metadata("pay_and_browse"),
        )
        runtime.record_payment_settled(
            task,
            paid_execution.payment_metadata,
            metadata=_temporal_metadata("pay_and_browse"),
        )
        repo.add_execution_result(paid_execution.execution)
        repo.set_task_status(task_row, "completed")
        repo.set_job_status(job, "awaiting_verification")
        return paid_execution.execution.model_dump()


@activity.defn
async def verify_result(job_id: str, task_id: str, execution_data: dict[str, Any]) -> dict[str, Any]:
    _, verifier_client, _ = _clients()
    with SessionLocal() as db:
        repo = PlannerRepository(db)
        job = repo.get_job(job_id)
        planner_run = repo.get_planner_run(job_id)
        task_row = repo.get_task(task_id)
        if job is None or planner_run is None or task_row is None:
            raise ValueError("Task not found")
        task = repo.task_payload(task_row)
        runtime = PlannerAgentRuntime(repo, planner_run)
        runtime.tool_call(
            task,
            "verify_result",
            f"Sending captured evidence to verifier for {task.allowed_domain}.",
            metadata=_temporal_metadata("verify_result"),
        )
        verification = repo.get_verification_result(task_id)
        if verification is None:
            execution = repo.get_execution_result(task_id) or ExecutionResultPayload.model_validate(execution_data)
            verification = await verifier_client.verify(task, execution)
            repo.add_verification_result(verification)
        runtime.record_verification(task, verification, metadata=_temporal_metadata("verify_result"))
        if verification.passed:
            repo.set_task_status(task_row, "verification_passed")
            repo.set_job_status(job, "verified")
        else:
            repo.set_task_status(task_row, "verification_failed")
            repo.set_job_status(job, "verification_failed")
        return verification.model_dump()


@activity.defn
async def settle_task(
    job_id: str,
    task_id: str,
    quote_data: dict[str, Any],
    verification_data: dict[str, Any],
    execution_data: dict[str, Any],
    funded_metadata: dict[str, Any],
) -> dict[str, Any]:
    _, _, settlement_client = _clients()
    settlement = build_settlement_adapter()
    quote = QuotePayload.model_validate(quote_data)
    with SessionLocal() as db:
        repo = PlannerRepository(db)
        job = repo.get_job(job_id)
        planner_run = repo.get_planner_run(job_id)
        task_row = repo.get_task(task_id)
        if job is None or planner_run is None or task_row is None:
            raise ValueError("Task not found")
        task = repo.task_payload(task_row)
        verification = repo.get_verification_result(task_id) or verification_data
        execution = repo.get_execution_result(task_id) or execution_data
        if isinstance(verification, dict):
            verification = VerificationResultPayload.model_validate(verification)
        if isinstance(execution, dict):
            execution = ExecutionResultPayload.model_validate(execution)
        if verification is None or execution is None:
            raise ValueError("Missing execution artifacts")
        existing_event = repo.get_settlement_event(task_id, "released" if verification.passed else "refunded")
        if existing_event is not None:
            return {"event_type": existing_event.event_type, "metadata": existing_event.metadata}
        runtime = PlannerAgentRuntime(repo, planner_run)
        settlement_decision = settlement.decide(task, quote, verification)
        if settings.settlement_mode == "alkahest":
            settlement_decision.metadata = await settlement_client.settle(
                task,
                quote,
                verification,
                execution,
                funded_metadata,
            )
        runtime.tool_call(
            task,
            "settle_payment",
            f"Settling task as {settlement_decision.event_type} after verification for {task.allowed_domain}.",
            metadata=_temporal_metadata("settle_task"),
        )
        repo.add_settlement_event(
            SettlementEventPayload(
                task_id=task.id,
                event_type=settlement_decision.event_type,
                amount_usdc=quote.price_usdc,
                timestamp=utc_now_iso(),
                metadata=settlement_decision.metadata,
            )
        )
        if settlement_decision.event_type == "released":
            repo.set_job_status(job, "released")
        else:
            repo.set_job_status(job, "refunded")
        return {"event_type": settlement_decision.event_type, "metadata": settlement_decision.metadata}


@activity.defn
async def finalize_job(job_id: str) -> dict[str, Any]:
    with SessionLocal() as db:
        repo = PlannerRepository(db)
        job = repo.get_job(job_id)
        planner_run = repo.get_planner_run(job_id)
        if job is None or planner_run is None:
            raise ValueError("Job not found")
        verifications = repo.list_verification_results([task.id for task in repo.get_tasks(job_id)])
        released = bool(verifications) and all(result.passed for result in verifications)
        runtime = PlannerAgentRuntime(repo, planner_run)
        runtime.finish(released=released, metadata=_temporal_metadata("finalize_job"))
        repo.update_planner_run(
            planner_run,
            workflow_status="completed",
            current_activity="completed",
        )
        repo.set_job_status(job, "released" if released else "refunded")
        return {"released": released}
