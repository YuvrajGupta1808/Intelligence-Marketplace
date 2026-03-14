---
name: build-fastapi-endpoint
description: Create or modify FastAPI endpoints, request and response models, validation, tests, or route wiring for planner-api, browser-worker, and verifier-api. Use when adding a new route, changing JSON contracts, introducing a service layer, or wiring health and persistence checks for these services.
---

# Build FastAPI Endpoint

Create Pydantic models first, route handlers second, service functions third, and tests fourth.

## Workflow

1. Define request and response models before touching handlers.
2. Keep route handlers thin and move orchestration into `services/`.
3. Return structured JSON only, including structured errors.
4. Add or update a health endpoint when introducing a new service surface.
5. Update README run instructions when a dependency or command changes.

## Guardrails

- Do not put payment logic directly in handlers.
- Do not let persistence models leak into API responses without explicit schemas.
- Keep timestamps in ISO 8601 UTC.
- Prefer deterministic service behavior over hidden side effects.

