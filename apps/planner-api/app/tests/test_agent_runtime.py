from app.db.database import Base, SessionLocal, engine
from app.models.schemas import JobCreateRequest
from app.services.agent_runtime import PlannerAgentRuntime
from app.services.planner import PlannerPlan
from app.services.repository import PlannerRepository


def test_planner_runtime_bootstrap_persists_trace():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        repo = PlannerRepository(db)
        job, task_rows = repo.create_job(
            JobCreateRequest(
                goal="Compare starter pricing pages",
                target_urls=["https://example.com/pricing", "https://openai.com/pricing"],
                max_budget_usdc=1.0,
            )
        )
        planner_run = repo.get_planner_run(job.id)
        assert planner_run is not None
        runtime = PlannerAgentRuntime(repo, planner_run)
        runtime.bootstrap(
            job.goal,
            [repo.task_payload(task) for task in task_rows],
            PlannerPlan(
                rationale_summary="Plan from deterministic fallback.",
                decision_log=["Use the supplied URLs.", "Run quote then browse then verify."],
                selected_workers=["browser-1"],
                execution_order=[task.id for task in task_rows],
                settlement_policy="Release on pass, refund on fail.",
                provider="deterministic",
            ),
        )
        detail_run = repo.get_planner_run(job.id)
        events = repo.list_trace_events(planner_run.id)
        assert detail_run is not None
        assert detail_run.planner_status == "planning"
        assert detail_run.current_step == "decompose_goal"
        assert detail_run.workflow_status == "running"
        assert detail_run.current_activity == "generate_plan"
        assert len(events) == 1
        assert events[0].event_type == "plan_created"
