# Proof Checklist

Use this checklist to prove that Proof-of-Browse is running with live integrations instead of demo fallbacks.

## Required inputs

Set these in your root `.env`:

```bash
APP_MODE=real
PLANNER_PROVIDER=openai
PAYMENT_MODE=real
SETTLEMENT_MODE=alkahest

OPENAI_API_KEY=

X402_SOLANA_PRIVATE_KEY=
X402_PAY_TO=

ALKAHEST_RPC_URL=
ALKAHEST_BUYER_PRIVATE_KEY=
ALKAHEST_WORKER_PRIVATE_KEY=
ALKAHEST_ORACLE_PRIVATE_KEY=
```

You also need:
- local Unbrowse running at `UNBROWSE_URL`
- a funded Solana devnet payer wallet
- a valid x402 payee address
- funded Base Sepolia buyer, worker, and oracle wallets

## Start

```bash
./run.sh real
```

Open:
- Web app: `http://127.0.0.1:3000`
- Temporal UI: `http://127.0.0.1:8088`

## Proof steps

1. Create a job with one pricing URL.
2. Run the job.
3. Open the workflow in Temporal UI.
4. Open the same job in the web app.

## What must be true

### OpenAI planner
- `plan_created` exists in `trace_events`
- `trace_events[].metadata.provider` is `openai`
- there is no deterministic fallback

### Unbrowse
- `execution_results[].provider` is `unbrowse`
- `execution_results[].provider_run_id` is non-empty
- `execution_results[].provider_metadata` contains Unbrowse fields
- if Unbrowse is unavailable, task execution fails instead of falling back to another executor

### x402 / Solana
- `payment_challenged` exists
- `payment_settled` exists
- payment metadata shows `payment_mode: real`
- payment metadata includes `payment_response_header`

### Alkahest
- settlement metadata contains:
  - `escrow_uid`
  - `fund_tx_hash`
  - `arbitration_decision_tx_hash`
  - `collect_tx_hash` on success or `reclaim_tx_hash` on refund

### Workflow
- Temporal workflow completes successfully
- the web app workflow panel shows the same workflow ID and final status

## Minimum success condition

One run is fully proven only if all of these are true:
- planner provider is `openai`
- execution provider is `unbrowse`
- payment mode is `real`
- settlement includes live Alkahest tx hashes
- Temporal UI shows the completed workflow
