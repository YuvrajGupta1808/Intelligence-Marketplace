---
name: verifier-rules
description: Implement or update deterministic verification logic, evidence checks, pass or fail scoring, and machine-readable failure reasons for verifier-api. Use when changing verification policy, required evidence fields, excerpt support logic, or branch coverage for verifier tests.
---

# Verifier Rules

Prefer deterministic checks and machine-readable outcomes.

## Rules

- Return explicit reasons for every failure branch.
- Keep scoring explainable from rule results.
- Test pass and fail cases for every rule branch.
- Avoid fuzzy heuristics unless the product explicitly requires them.

