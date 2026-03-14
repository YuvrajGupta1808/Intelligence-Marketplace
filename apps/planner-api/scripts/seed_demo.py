from __future__ import annotations

from app.core.time import utc_now_iso
from app.db.database import SessionLocal
from app.models.schemas import ExecutionResultPayload, JobCreateRequest, QuotePayload, SettlementEventPayload, VerificationResultPayload
from app.services.repository import PlannerRepository


def main() -> None:
    with SessionLocal() as db:
        repo = PlannerRepository(db)
        success_job, success_tasks = repo.create_job(
            JobCreateRequest(
                goal="Compare pricing pages for 3 vendors.",
                target_urls=[
                    "https://example.com/pricing",
                    "https://openai.com/pricing",
                    "https://vercel.com/pricing",
                ],
                max_budget_usdc=1.0,
            )
        )
        failed_job, failed_tasks = repo.create_job(
            JobCreateRequest(
                goal="Compare pricing pages for 1 vendor and trigger a failed verification.",
                target_urls=["https://example.com/pricing"],
                max_budget_usdc=0.2,
            )
        )
        failed_task = repo.task_payload(failed_tasks[0])
        quote = QuotePayload(
            worker_id="browser-1",
            task_id=failed_task.id,
            price_usdc=0.05,
            eta_sec=20,
            capabilities=["extract_pricing", "screenshot", "html_hash"],
        )
        repo.add_quote(quote)
        repo.add_execution_result(
            ExecutionResultPayload(
                task_id=failed_task.id,
                site="example.com",
                final_url="https://example.com/pricing",
                plan_name="Starter",
                price_found="",
                timestamp=utc_now_iso(),
                evidence={
                    "screenshot_url": "http://localhost:8002/artifacts/failed-task.png",
                    "html_hash": "sha256:bad",
                    "excerpt": "Starter plan details missing the price.",
                },
            )
        )
        repo.add_verification_result(
            VerificationResultPayload(
                task_id=failed_task.id,
                passed=False,
                score=0.49,
                reasons=["missing_required_field", "excerpt_not_supportive"],
                details={"missing_required_field": "price_found"},
            )
        )
        repo.add_settlement_event(
            SettlementEventPayload(
                task_id=failed_task.id,
                event_type="refunded",
                amount_usdc=0.05,
                timestamp=utc_now_iso(),
                metadata={"worker_id": "browser-1"},
            )
        )
        repo.set_job_status(success_job, "created")
        repo.set_job_status(failed_job, "refunded")
    print("Seeded demo job.")


if __name__ == "__main__":
    main()
