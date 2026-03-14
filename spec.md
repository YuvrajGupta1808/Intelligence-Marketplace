# Proof-of-Browse Spec

## Summary

Proof-of-Browse is a multi-service app for paid browser work.

The target product is:
- a planner agent that interprets a user goal
- a browser worker that performs live web work
- a verifier that checks evidence deterministically
- a payment and escrow flow that records settlement
- a frontend that shows planner decisions, worker outputs, and settlement state

This spec is the source of truth for the next implementation pass.

## Current Reality

The repo is not yet the full product.

What exists today:
- Next.js frontend
- `planner-api` FastAPI service
- `browser-worker` FastAPI service with Playwright
- `verifier-api` FastAPI service
- persisted jobs, tasks, quotes, execution results, verification results, settlement events
- planner trace persistence and planner trace UI
- mock x402-style challenge and retry flow
- OpenAI planner integration path via the Responses API when configured
- Alkahest-compatible settlement metadata mode for sponsor demos

What does not exist yet:
- no real platform SDK/API integration for the referenced ecosystem pieces
- no true multi-agent runtime
- no worker discovery or negotiation beyond one configured worker
- no fully on-chain Alkahest settlement transaction flow in active use

Because of that, the current app should be treated as a partial backend-driven MVP, not a complete platform.

## Product Goal

Build a complete working app where:
- a user submits a research or comparison goal
- a planner agent uses an LLM to create and adapt a task plan
- the planner selects and invokes worker tools
- the browser worker performs live browsing and returns structured evidence
- the verifier determines pass or fail using deterministic checks
- the planner settles release or refund
- the frontend renders the full run, including planner reasoning trace and final settlement

## Core Principles

- The planner is the actual agent.
- The browser worker is a deterministic tool runtime, not the primary agent.
- The verifier is deterministic first.
- Every user-visible state must come from persisted backend state.
- All APIs return structured JSON.
- The frontend must not claim integrations that are not actually live.
- If an API or SDK is not wired, the UI and docs must say so clearly.

## Required End State

### 1. Planner Agent

The planner must:
- call a real LLM API
- interpret a goal plus explicit input URLs
- produce a plan with task rationale
- choose an execution order
- invoke tool actions instead of using a fixed hardcoded loop
- persist trace events for every meaningful decision and tool call
- decide release or refund based on verification outcome

Minimum tool actions:
- `create_plan`
- `request_quote`
- `request_browse`
- `verify_result`
- `settle_payment`

The planner does not need autonomous internet discovery in the first complete version.

### 2. Browser Worker

The browser worker must:
- expose `POST /quote`
- expose paid `POST /browse`
- browse live URLs with Playwright
- capture screenshot, final URL, excerpt, HTML hash, timestamp
- save artifacts before returning
- return structured JSON only

The worker may remain deterministic and non-LLM in the execution path.

### 3. Verifier

The verifier must:
- expose `POST /verify`
- check screenshot presence
- check allowed-domain match
- check required fields
- check excerpt support
- check HTML hash
- check timestamp
- check deadline
- return pass or fail, score, and machine-readable reasons

### 4. Payments and Settlement

The payment system must:
- preserve the HTTP-native 402 challenge pattern
- support mock mode for local development
- keep real payment mode behind an adapter
- log challenge, retry, verification, release, and refund steps

The escrow system must:
- persist state transitions
- support `pending`, `funded`, `released`, `refunded`, `disputed`
- log all settlement events

### 5. Frontend

The frontend must show:
- job creation
- task board
- evidence
- settlement timeline
- planner trace
- current planner step
- selected workers
- decision log

The frontend must visualize the actual backend state, not mock data.

## Required External Integrations

### OpenAI

The planner supports a real OpenAI API call for planner behavior when configured.

Preferred default:
- OpenAI Responses API

Alternative:
- OpenAI Agents SDK if it fits the repo structure better

The planner must not be described as an AI agent unless this integration is live.

Default local behavior may still fall back to the deterministic planner if the API key is absent.

### Platform Integrations

The next implementation pass must wire the actual platform or protocol clients that are intended to define this product.

At minimum:
- use the real OpenAI integration
- keep x402 behind the existing adapter surface
- only claim external platform integrations once the repo actually calls them

If a referenced platform package is not used in runtime code, remove or clearly mark the claim in UI and docs.

## APIs

### Planner API

Required endpoints:
- `POST /health`
- `POST /jobs`
- `GET /jobs/{id}`
- `POST /jobs/{id}/run`

`GET /jobs/{id}` must include:
- `job`
- `planner_run`
- `trace_events`
- `tasks`
- `quotes`
- `execution_results`
- `verification_results`
- `settlement_events`

### Browser Worker

Required endpoints:
- `GET /health`
- `POST /quote`
- `POST /browse`

### Verifier API

Required endpoints:
- `GET /health`
- `POST /verify`

## Persistence

The system must persist:
- jobs
- planner runs
- trace events
- tasks
- quotes
- execution results
- verification results
- settlement events

Postgres remains the source of truth.

Redis may be used for queueing or transient execution coordination, but not as the source of truth.

## Data Contracts

The canonical business objects are:
- `Job`
- `PlannerRun`
- `TraceEvent`
- `Task`
- `Quote`
- `ExecutionResult`
- `VerificationResult`
- `SettlementEvent`

Shared schemas must remain in `packages/shared-schemas`.

## Non-Goals For The Next Pass

- multi-tenant auth
- worker reputation systems
- internet-scale worker discovery
- fully autonomous negotiation
- production wallet UX
- onchain escrow as a hard requirement
- generalized arbitrary browser workflow authoring

## Implementation Requirements

- remove misleading product claims when integrations are not real
- keep payment adapters isolated
- keep worker and verifier deterministic unless explicitly expanded
- keep trace events machine-readable and user-visible
- use typed request and response models across services
- update README and docs whenever architecture changes

## Acceptance Criteria

The app is only considered complete when all of these are true:

- the planner calls a real AI API
- the planner execution is tool-driven, not a fixed local loop
- the browser worker performs live browsing and returns real evidence
- the verifier returns deterministic pass or fail results
- the payment flow demonstrates 402 challenge and retry
- the frontend shows the real planner trace and settlement state
- no UI section depends on mock-only data without being labeled as such
- product claims in README and UI match what the code actually does

## Recommended Next Build Order

1. wire OpenAI into `planner-api`
2. convert planner execution from fixed orchestration to model-guided tool use
3. preserve existing worker, verifier, and payment adapters as planner tools
4. update frontend copy to reflect real planner-agent behavior
5. wire additional platform integrations only after their runtime use is real

## Repo Guidance For The Next Chat

Use this file as the primary product spec.

The next chat should assume:
- current repo state is a partial MVP
- planner trace exists already
- the main missing requirement is real AI and real platform integration
- the planner is the correct place to make the app genuinely agentic
