from __future__ import annotations

import asyncio

from app.core.config import settings
from app.temporal import activities
from app.temporal.workflows import ProofOfBrowseWorkflow


async def main() -> None:
    from temporalio.client import Client
    from temporalio.worker import Worker

    client = await Client.connect(settings.temporal_target, namespace=settings.temporal_namespace)
    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=[ProofOfBrowseWorkflow],
        activities=[
            activities.generate_plan,
            activities.request_quote,
            activities.fund_escrow,
            activities.pay_and_browse,
            activities.verify_result,
            activities.settle_task,
            activities.finalize_job,
        ],
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
