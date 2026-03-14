# Demo Script

## Terminal setup

```bash
docker compose -f infra/docker-compose.yml up -d

cd apps/planner-api && source .venv/bin/activate && uvicorn app.main:app --reload --port 8001
cd apps/planner-api && source .venv/bin/activate && python -m app.temporal.worker
cd apps/browser-worker && source .venv/bin/activate && uvicorn app.main:app --reload --port 8002
cd apps/verifier-api && source .venv/bin/activate && uvicorn app.main:app --reload --port 8003
cd apps/sponsor-runtime && npm run dev
cd apps/web && npm run dev
```

## Demo prompt

Use:

`Compare pricing pages for 3 vendors.`

URLs:

- `https://example.com/pricing`
- `https://openai.com/pricing`
- `https://vercel.com/pricing`

## Click path

1. Open the create job screen.
2. Paste the URLs and submit.
3. Open the job detail screen.
4. Click `Run Job`.
5. Point to the Workflow Execution panel and then open Temporal UI on `http://localhost:8088`.
6. Open a successful task card and show the evidence drawer.
7. Open a failed task and show the refund state.
8. Point to the settlement timeline.

## Demo narration

- "The planner API starts a Temporal workflow, and each agent interaction is a visible workflow activity."
- "Each task gets a quote before funding."
- "The worker exposes a paid HTTP endpoint and answers with a 402 challenge first."
- "Temporal shows where the workflow is running or breaking while the app mirrors the same persisted state."
- "Passing tasks release escrow. Failing tasks refund automatically."
