---
name: x402-integration
description: Implement, refactor, or test x402-protected routes, buyer logic, facilitator-backed payment adapters, or payment verification flows for planner-api and browser-worker. Use when adding 402 challenge handling, payment headers, mock-versus-real adapters, or integration tests for 402 to pay to 200 behavior.
---

# X402 Integration

Keep all payment behavior behind an adapter interface.

## Rules

- Support two modes: `mock` and `real`.
- Mock mode must not require a wallet or facilitator.
- Real mode must target Solana devnet first.
- Keep route handlers unaware of concrete payment implementations.
- Log challenge received, payment sent, verification result, and settlement result.
- Add at least one integration test for the 402 to retry to success flow.

## Implementation order

1. Define shared protocols for planner payment clients and worker payment gates.
2. Implement mock mode first and make it the default.
3. Add real-mode configuration behind a feature flag without disturbing mock tests.
4. Keep request and response payloads identical across modes.

