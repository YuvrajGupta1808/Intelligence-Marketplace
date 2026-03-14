CREATE TABLE IF NOT EXISTS jobs (
  id VARCHAR(36) PRIMARY KEY,
  goal TEXT NOT NULL,
  status VARCHAR(64) NOT NULL,
  max_budget_usdc FLOAT NOT NULL,
  created_at VARCHAR(64) NOT NULL
);

CREATE TABLE IF NOT EXISTS planner_runs (
  id VARCHAR(36) PRIMARY KEY,
  job_id VARCHAR(36) NOT NULL UNIQUE REFERENCES jobs(id),
  planner_status VARCHAR(64) NOT NULL,
  current_step VARCHAR(128) NOT NULL,
  rationale_summary TEXT NOT NULL,
  selected_workers_json TEXT NOT NULL,
  decision_log_json TEXT NOT NULL,
  updated_at VARCHAR(64) NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
  id VARCHAR(36) PRIMARY KEY,
  job_id VARCHAR(36) NOT NULL REFERENCES jobs(id),
  task_type VARCHAR(64) NOT NULL,
  target_url TEXT NOT NULL,
  allowed_domain VARCHAR(255) NOT NULL,
  required_fields TEXT NOT NULL,
  status VARCHAR(64) NOT NULL,
  deadline_seconds INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS quotes (
  id VARCHAR(36) PRIMARY KEY,
  worker_id VARCHAR(64) NOT NULL,
  task_id VARCHAR(36) NOT NULL REFERENCES tasks(id),
  price_usdc FLOAT NOT NULL,
  eta_sec INTEGER NOT NULL,
  capabilities TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS execution_results (
  id VARCHAR(36) PRIMARY KEY,
  task_id VARCHAR(36) NOT NULL REFERENCES tasks(id),
  payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS verification_results (
  id VARCHAR(36) PRIMARY KEY,
  task_id VARCHAR(36) NOT NULL REFERENCES tasks(id),
  payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settlement_events (
  id VARCHAR(36) PRIMARY KEY,
  task_id VARCHAR(36) NOT NULL REFERENCES tasks(id),
  event_type VARCHAR(64) NOT NULL,
  amount_usdc FLOAT NOT NULL,
  timestamp VARCHAR(64) NOT NULL,
  metadata_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS trace_events (
  id VARCHAR(36) PRIMARY KEY,
  planner_run_id VARCHAR(36) NOT NULL REFERENCES planner_runs(id),
  job_id VARCHAR(36) NOT NULL REFERENCES jobs(id),
  task_id VARCHAR(36) REFERENCES tasks(id),
  event_type VARCHAR(64) NOT NULL,
  title VARCHAR(128) NOT NULL,
  detail TEXT NOT NULL,
  metadata_json TEXT NOT NULL,
  created_at VARCHAR(64) NOT NULL
);
