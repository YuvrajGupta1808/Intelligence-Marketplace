from __future__ import annotations

from dataclasses import dataclass

from app.core.time import utc_now_iso
from app.db.models import PlannerRunModel
from app.models.schemas import QuotePayload, TaskPayload, TraceEventPayload, VerificationResultPayload
from app.services.repository import PlannerRepository
from app.services.planner import PlannerPlan
from app.db.models import uuid_str


@dataclass
class PlanStep:
    step_id: str
    task_id: str | None
    tool_name: str
    title: str
    detail: str


class PlannerAgentRuntime:
    def __init__(self, repo: PlannerRepository, planner_run: PlannerRunModel) -> None:
        self.repo = repo
        self.planner_run = planner_run
        self.decision_log: list[str] = []

    def bootstrap(self, goal: str, tasks: list[TaskPayload], plan: PlannerPlan, metadata: dict | None = None) -> None:
        self.decision_log = list(plan.decision_log)
        self.repo.update_planner_run(
            self.planner_run,
            planner_status="planning",
            current_step="decompose_goal",
            workflow_status="running",
            current_activity="generate_plan",
            rationale_summary=plan.rationale_summary,
            selected_workers=plan.selected_workers,
            decision_log=self.decision_log,
        )
        self._trace(
            task_id=None,
            event_type="plan_created",
            title="Planner decomposed the job",
            detail=f"Created {len(tasks)} browse tasks from the supplied URL list using the {plan.provider} planner.",
            metadata={"task_count": len(tasks), "provider": plan.provider, "goal": goal, **(metadata or {})},
        )

    def tool_call(self, task: TaskPayload | None, tool_name: str, detail: str, metadata: dict | None = None) -> None:
        current_step = tool_name
        self.decision_log.append(detail)
        self.repo.update_planner_run(
            self.planner_run,
            planner_status="running",
            current_step=current_step,
            current_activity=tool_name,
            workflow_status="running",
            decision_log=self.decision_log,
        )
        self._trace(
            task_id=task.id if task else None,
            event_type="tool_call",
            title=f"Planner invoked {tool_name}",
            detail=detail,
            metadata={"tool_name": tool_name, **(metadata or {})},
        )

    def record_quote(self, task: TaskPayload, quote: QuotePayload, metadata: dict | None = None) -> None:
        self._trace(
            task_id=task.id,
            event_type="quote_received",
            title="Worker quote received",
            detail=f"Quoted {quote.price_usdc} USDC for {task.allowed_domain}.",
            metadata={"worker_id": quote.worker_id, "price_usdc": quote.price_usdc, **(metadata or {})},
        )

    def record_payment_challenge(
        self,
        task: TaskPayload,
        payment_metadata: dict[str, object],
        metadata: dict | None = None,
    ) -> None:
        self._trace(
            task_id=task.id,
            event_type="payment_challenged",
            title="Worker required payment",
            detail=f"Received 402 challenge before browsing {task.allowed_domain}.",
            metadata={"task_type": task.task_type, **payment_metadata, **(metadata or {})},
        )

    def record_payment_settled(
        self,
        task: TaskPayload,
        payment_metadata: dict[str, object],
        metadata: dict | None = None,
    ) -> None:
        self._trace(
            task_id=task.id,
            event_type="payment_settled",
            title="x402 payment completed",
            detail=f"Settled paid browse access for {task.allowed_domain}.",
            metadata={"task_type": task.task_type, **payment_metadata, **(metadata or {})},
        )

    def record_verification(
        self,
        task: TaskPayload,
        verification: VerificationResultPayload,
        metadata: dict | None = None,
    ) -> None:
        status = "passed" if verification.passed else "failed"
        self._trace(
            task_id=task.id,
            event_type="verification_result",
            title=f"Verification {status}",
            detail=f"Verifier {status} task with reasons: {', '.join(verification.reasons)}.",
            metadata={"passed": verification.passed, **(metadata or {})},
        )

    def finish(self, released: bool, metadata: dict | None = None) -> None:
        final_state = "completed" if released else "attention_required"
        final_step = "released" if released else "refunded"
        self.repo.update_planner_run(
            self.planner_run,
            planner_status=final_state,
            current_step=final_step,
            workflow_status="completed",
            current_activity="completed",
            decision_log=self.decision_log,
        )
        self._trace(
            task_id=None,
            event_type="plan_finished",
            title="Planner completed execution",
            detail=f"Planner finished with final settlement state {final_step}.",
            metadata={"released": released, **(metadata or {})},
        )

    def _trace(self, *, task_id: str | None, event_type: str, title: str, detail: str, metadata: dict) -> None:
        self.repo.add_trace_event(
            TraceEventPayload(
                id=uuid_str(),
                planner_run_id=self.planner_run.id,
                job_id=self.planner_run.job_id,
                task_id=task_id,
                event_type=event_type,
                title=title,
                detail=detail,
                metadata=metadata,
                created_at=utc_now_iso(),
            )
        )
