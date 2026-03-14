ALTER TABLE planner_runs ADD COLUMN IF NOT EXISTS workflow_id VARCHAR(255);
ALTER TABLE planner_runs ADD COLUMN IF NOT EXISTS workflow_run_id VARCHAR(255);
ALTER TABLE planner_runs ADD COLUMN IF NOT EXISTS workflow_status VARCHAR(64) NOT NULL DEFAULT 'not_started';
ALTER TABLE planner_runs ADD COLUMN IF NOT EXISTS current_activity VARCHAR(128) NOT NULL DEFAULT 'awaiting_run';
