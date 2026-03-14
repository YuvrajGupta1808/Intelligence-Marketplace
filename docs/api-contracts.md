# API Contracts

## Planner API

### `POST /health`
Response:

```json
{"status":"ok","service":"planner-api"}
```

### `POST /jobs`
Request:

```json
{
  "goal": "Compare pricing pages for 3 vendors",
  "target_urls": [
    "https://example.com/pricing",
    "https://openai.com/pricing",
    "https://vercel.com/pricing"
  ],
  "max_budget_usdc": 1.0
}
```

Response:

```json
{
  "job_id": "uuid",
  "status": "created",
  "task_ids": ["uuid"]
}
```

### `GET /jobs/{id}`
Response:

```json
{
  "job": {},
  "planner_run": {},
  "workflow": {
    "workflow_id": "proof-of-browse-uuid",
    "run_id": "uuid",
    "workflow_status": "running",
    "current_activity": "pay_and_browse",
    "namespace": "default",
    "task_queue": "proof-of-browse",
    "temporal_ui_url": "http://localhost:8088"
  },
  "trace_events": [],
  "tasks": [],
  "execution_results": [],
  "quotes": [],
  "verification_results": [],
  "settlement_events": []
}
```

### `POST /jobs/{id}/run`
Response:

```json
{
  "job_id": "uuid",
  "status": "queued",
  "workflow": {
    "workflow_id": "proof-of-browse-uuid",
    "run_id": "uuid",
    "workflow_status": "queued",
    "current_activity": "awaiting_worker",
    "namespace": "default",
    "task_queue": "proof-of-browse",
    "temporal_ui_url": "http://localhost:8088"
  },
  "report": {}
}
```

### `GET /jobs/{id}/workflow`
Response:

```json
{
  "job_id": "uuid",
  "workflow_id": "proof-of-browse-uuid",
  "run_id": "uuid",
  "workflow_status": "running",
  "current_activity": "verify_result",
  "namespace": "default",
  "task_queue": "proof-of-browse",
  "temporal_ui_url": "http://localhost:8088"
}
```

### `POST /jobs/{id}/run`
Failure response:

```json
{
  "detail": "Temporal server unavailable"
}
```

### `GET /jobs/{id}`
Trace event metadata now includes Temporal execution identifiers:

```json
{
  "event_type": "payment_settled",
  "metadata": {
    "workflow_engine": "temporal",
    "workflow_id": "proof-of-browse-uuid",
    "workflow_run_id": "uuid",
    "activity_type": "pay_and_browse",
    "activity_attempt": 1
  }
}
```

## Browser worker

### `GET /health`
Response:

```json
{"status":"ok","service":"browser-worker"}
```

### `POST /quote`
Request:

```json
{
  "task_id": "uuid",
  "task_type": "extract_pricing",
  "target_url": "https://example.com/pricing",
  "allowed_domain": "example.com",
  "required_fields": ["plan_name", "price_found"]
}
```

Response:

```json
{
  "worker_id": "browser-1",
  "task_id": "uuid",
  "price_usdc": 0.05,
  "eta_sec": 20,
  "capabilities": ["extract_pricing","screenshot","html_hash"]
}
```

### `POST /browse`
402 response:

```json
{
  "detail": {
    "error": "payment_required",
    "payment_mode": "mock",
    "challenge": "mock-usdc-challenge"
  }
}
```

Success response:

```json
{
  "task_id": "uuid",
  "site": "example.com",
  "final_url": "https://example.com/pricing",
  "plan_name": "Starter",
  "price_found": "$49/mo",
  "timestamp": "2026-03-13T20:03:00Z",
  "provider": "unbrowse",
  "provider_run_id": "trace_123",
  "provider_status": "live-capture",
  "provider_metadata": {
    "skill_id": "skill_123",
    "source": "live-capture"
  },
  "evidence": {
    "screenshot_url": "http://localhost:8002/artifacts/task.png",
    "html_hash": "sha256:abc123",
    "excerpt": "Starter plan starts at $49/mo"
  }
}
```

## Sponsor runtime

### `GET /health`
Response:

```json
{"status":"ok","service":"sponsor-runtime","browser_worker_healthy":true}
```

### `POST /quote`
Response:

```json
{
  "worker_id": "unbrowse-browser-agent",
  "task_id": "uuid",
  "price_usdc": 0.06,
  "eta_sec": 20,
  "capabilities": ["extract_pricing","screenshot","html_hash","unbrowse","x402","alkahest"]
}
```

## Verifier API

### `GET /health`
Response:

```json
{"status":"ok","service":"verifier-api"}
```

### `POST /verify`
Request:

```json
{
  "task": {},
  "execution_result": {}
}
```

Response:

```json
{
  "task_id": "uuid",
  "passed": true,
  "score": 1.0,
  "reasons": ["screenshot_present","domain_match","excerpt_match","hash_present"]
}
```

## Sample errors

```json
{
  "code": "domain_mismatch",
  "message": "Execution result final_url does not match the allowed domain.",
  "details": {
    "allowed_domain": "example.com",
    "final_url": "https://other.com"
  }
}
```
