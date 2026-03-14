from app.db.database import Base, SessionLocal, engine
from app.models.schemas import JobCreateRequest
from app.services.repository import PlannerRepository


def test_task_creation_and_defaults():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        repo = PlannerRepository(db)
        job, tasks = repo.create_job(
            JobCreateRequest(
                goal="Compare pricing pages",
                target_urls=["https://example.com/pricing"],
                max_budget_usdc=1.0,
            )
        )
        assert job.status == "created"
        assert tasks[0].status == "pending"
        assert tasks[0].allowed_domain == "example.com"
        planner_run = repo.get_planner_run(job.id)
        assert planner_run is not None
        assert planner_run.workflow_status == "not_started"
        assert planner_run.current_activity == "awaiting_run"
