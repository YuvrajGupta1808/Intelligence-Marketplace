# Proof-of-Browse Agent Instructions

You are building a hackathon MVP called Proof-of-Browse.

## Product purpose
Build a planner agent that hires browser agents to perform paid web tasks using x402 on Solana devnet, verifies the evidence, and settles escrow.

## Global engineering rules
- Prefer the smallest working implementation.
- Never change architecture without updating README and architecture docs.
- Never leave TODO comments for core flows.
- Every API must have request/response schemas.
- Every service must have a health endpoint.
- All dates must be ISO 8601 UTC.
- All user-visible job states must come from persisted backend state, not transient frontend assumptions.
- Browser-worker returns structured JSON only.
- Verifier logic is deterministic first.
- Keep x402 integration behind an adapter so mock and real modes share one interface.
- Use type-safe schemas across frontend and backend where practical.

## Delivery rules
For every phase:
1. implement code
2. add or update tests
3. update README
4. print changed files
5. explain how to run the phase locally

## OpenAI/Codex rules
Always use the OpenAI developer documentation MCP server for any OpenAI, Codex, MCP, or API question before using any other source.

## Payment rules
- Use app-level escrow first.
- On-chain escrow is optional and only after MVP works.
- Planner controls state transitions for funded, released, refunded, disputed.
- All payment events must be logged as settlement events.

## Verification rules
A task passes only if:
- screenshot exists
- final_url matches the allowed domain
- required fields are non-empty
- excerpt supports the extracted value
- html_hash exists
- timestamp exists

---

## Service map

| Service | Port | Health | Run command |
|---|---|---|---|
| planner-api | 8001 | `POST /health` | `uvicorn app.main:app --host 127.0.0.1 --port 8001` |
| temporal-worker | — | — | `python -m app.temporal.worker` |
| browser-worker | 8002 | `GET /health` | `uvicorn app.main:app --host 127.0.0.1 --port 8002` |
| verifier-api | 8003 | `GET /health` | `uvicorn app.main:app --host 127.0.0.1 --port 8003` |
| sponsor-runtime | 8010 | `GET /health` | `npm run dev` |
| web | 3000 | `GET /` | `next dev --hostname 127.0.0.1 --port 3000` |
| Temporal UI | 8088 | browser | Docker |

## Build and test commands

```bash
# Run everything (demo mode uses SQLite; no secrets needed)
./run.sh demo

# Run everything (real mode: requires OPENAI_API_KEY, X402 keys, Alkahest keys)
./run.sh real

# Python service: install deps + run tests
cd apps/<service>
pip install -e .[dev]
pytest

# Node service: install + run
cd apps/sponsor-runtime
npm install && npm run dev

# Next.js web app
cd apps/web
npm install && next dev --hostname 127.0.0.1 --port 3000

# Apply planner migrations (demo)
cd apps/planner-api
POSTGRES_URL=sqlite:///./proof-of-browse.db python scripts/migrate.py
```

## Architecture decisions

- `apps/planner-api` — FastAPI + SQLAlchemy 2.0. Owns the canonical job/task/settlement state. Launches and polls Temporal workflows. Migrations live in `migrations/*.sql` and run at startup via `scripts/migrate.py`.
- `apps/browser-worker` — FastAPI + Playwright + optional Unbrowse. Returns structured `BrowseResponse` JSON only. Never streams HTML in api responses.
- `apps/verifier-api` — FastAPI. Pure deterministic rules in `app/rules/engine.py`. No AI calls.
- `apps/sponsor-runtime` — Node/Express + `@x402/express` on `/browse`. Handles 402 payment middleware before proxying to browser-worker.
- `apps/web` — Next.js 15 App Router with `"use client"` on the page. Polls planner-api every 3 seconds. No server-side data fetching — client only.
- `packages/shared-schemas` — Shared TypeScript/JSON schema source of truth. Regenerate after changing schemas.

## Key code conventions

### Python services

**Models** — SQLAlchemy `Mapped` declarative style:
```python
class JobModel(Base):
    __tablename__ = "jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
```

**Schemas** — Every route has a Pydantic request/response model in `app/models/schemas.py`. Never return raw dicts from routes.

**Route pattern** — All routes in `app/api/routes.py`, registered on a single `APIRouter`. Database sessions via `Depends(get_db)`.

**Config** — Pydantic `BaseSettings` in `app/core/config.py`, loaded from `.env`. Real mode adds mandatory field validation. Never read env vars directly outside `config.py`.

**JSON storage** — Complex fields stored as JSON strings (`metadata_json`, `payload_json`, `decision_log_json`). Deserialize with Pydantic on read.

### Payment adapter

`PaymentGate` is a Protocol in `apps/browser-worker/app/core/payment.py`:
```python
class PaymentGate(Protocol):
    async def challenge_or_continue(self, request: Request) -> None: ...
```
`MockPaymentGate` and `RealPaymentGate` both implement it. Selected via `Depends(get_payment_gate)` based on `PAYMENT_MODE`. Never call real x402 from inside demo mode.

### Temporal activities

All activities live in `apps/planner-api/app/temporal/activities.py` and follow:
1. Load context from DB at start (idempotent — check for existing record before writing).
2. Call external service via httpx.
3. Persist result to DB.
4. Return a plain dict (must be JSON-serializable for Temporal).

Retry policies: `quote`, `fund`, `pay_and_browse`, `settle_task` have `maximum_attempts=3`. `verify_result` and `finalize_job` do not retry.

### Frontend

- `apps/web/lib/api.ts` is the only file allowed to call planner-api. All `fetch()` calls go here.
- Use `useTransition` for async actions that start a Temporal workflow.
- Use `useEffect` with 3-second interval polling for job status (no websockets).
- Never derive visible job state from frontend assumptions — always reflect what the API returns.

## Database and migration pitfalls

- **SQLite** (demo mode) does not support `ADD COLUMN IF NOT EXISTS`. `scripts/migrate.py` handles this with a `PRAGMA table_info` check — keep migration files compatible with this workaround.
- **Multi-statement SQL**: SQLite requires statements executed one at a time. `migrate.py` splits on `;`.
- **Demo mode** uses `sqlite:///./proof-of-browse.db` in `apps/planner-api/`. Real mode uses the `POSTGRES_URL` env var.
- `Base.metadata.create_all(bind=engine)` runs on every startup in `app/main.py` — this is a safety net, not the primary migration path.

## Environment configuration

Copy `.env.example` to `.env` at the repo root for the quickest start. Key variables:

| Variable | Demo default | Purpose |
|---|---|---|
| `APP_MODE` | `demo` | `demo` or `real` |
| `PLANNER_PROVIDER` | `auto` | `auto` (mock plan) or `openai` |
| `PAYMENT_MODE` | `mock` | `mock` or `real` |
| `SETTLEMENT_MODE` | `app` | `app` (in-memory) or `alkahest` |
| `POSTGRES_URL` | sqlite (set by run.sh) | DB connection string |
| `TEMPORAL_TASK_QUEUE` | `proof-of-browse` | Must match worker registration |
| `DEMO_ALLOWED_DOMAINS` | `example.com,openai.com,vercel.com` | Restrict browse targets in demo |

Real mode additionally requires: `OPENAI_API_KEY`, `X402_SOLANA_PRIVATE_KEY`, `X402_PAY_TO`, `ALKAHEST_RPC_URL`, `ALKAHEST_BUYER_PRIVATE_KEY`, `ALKAHEST_WORKER_PRIVATE_KEY`, `ALKAHEST_ORACLE_PRIVATE_KEY`.

## Test patterns

- All Python tests use pytest. Async tests use `pytest-asyncio`.
- Planner tests use an in-memory SQLite database created per test.
- Never mock the database in unit tests — use a real in-memory SQLite session.
- Mock external HTTP calls (worker, verifier) with `monkeypatch` or `httpx.MockTransport`.
- Verifier tests in `apps/verifier-api/app/tests/test_rules.py` exercise all rule paths: pass, domain mismatch, missing screenshot, missing required field, deadline exceeded.
- Browser worker tests in `apps/browser-worker/app/tests/test_worker.py` cover: quote pricing, screenshot paths, html hashing, and both 402 challenge modes.

## Settlement state machine

Planner controls all state transitions. No service other than planner-api may write settlement events.

```
funded → released   (verification passed)
funded → refunded   (verification failed or error)
funded → disputed   (manual override)
```

Only one terminal event (`released` or `refunded`) is allowed per task — the repository enforces uniqueness before writing.

