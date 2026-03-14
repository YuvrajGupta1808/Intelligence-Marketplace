# Proof-of-Browse PRD

## Problem
Most useful internet work lives behind websites rather than clean APIs. Agents need a safe way to buy browser labor, verify the evidence, and settle payment automatically.

## Users
- Hackathon judges
- Dev tools teams
- Research automation users
- Competitive intelligence users
- Procurement and comparison users

## Core user story
A user submits a request such as "Compare pricing pages for 3 AI products and tell me the monthly starter plan price." The planner creates deterministic tasks, gets a quote, pays the worker endpoint through x402, receives the evidence, asks the verifier to score it, and releases or refunds escrow.

## Scope
- Deterministic URL-based task creation
- One configured browser worker
- App-level escrow
- Mock x402 plus an isolated real adapter surface
- Live task board and evidence view

## Success metrics
- One prompt creates at least 3 subtasks
- Each subtask shows a quote
- Paid route returns 402 before payment
- Planner retries with payment and receives a result
- Verifier returns pass or fail and machine-readable reasons
- Escrow transitions are persisted and visible

## Non-goals
- Auth and multi-tenant access
- Internet-scale worker discovery
- On-chain escrow for MVP
- Arbitrary browser workflow authoring
- Production dispute resolution

