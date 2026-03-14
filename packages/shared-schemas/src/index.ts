export type JobStatus =
  | "created"
  | "quoted"
  | "funded"
  | "payment_challenged"
  | "payment_sent"
  | "running"
  | "awaiting_verification"
  | "verified"
  | "released"
  | "refunded"
  | "failed"
  | "disputed";

export type TaskStatus =
  | "pending"
  | "quoted"
  | "accepted"
  | "running"
  | "completed"
  | "verification_failed"
  | "verification_passed";

export interface JobInput {
  goal: string;
  target_urls: string[];
  max_budget_usdc: number;
}

export interface TaskRecord {
  id: string;
  job_id: string;
  task_type: "extract_pricing";
  target_url: string;
  allowed_domain: string;
  required_fields: string[];
  status: TaskStatus;
}

export interface QuoteRecord {
  worker_id: string;
  task_id: string;
  price_usdc: number;
  eta_sec: number;
  capabilities: string[];
}

export interface PlannerRun {
  id: string;
  job_id: string;
  planner_status: string;
  current_step: string;
  rationale_summary: string;
  selected_workers: string[];
  decision_log: string[];
  updated_at: string;
}

export interface TraceEvent {
  id: string;
  planner_run_id: string;
  job_id: string;
  task_id?: string;
  event_type: string;
  title: string;
  detail: string;
  metadata: Record<string, string | number | boolean>;
  created_at: string;
}

export interface ExecutionResult {
  task_id: string;
  site: string;
  final_url: string;
  plan_name: string;
  price_found: string;
  timestamp: string;
  provider: string;
  provider_run_id?: string;
  provider_status?: string;
  provider_metadata?: Record<string, string | number | boolean | null | object>;
  evidence: {
    screenshot_url: string;
    html_hash: string;
    excerpt: string;
  };
}

export interface VerificationResult {
  task_id: string;
  passed: boolean;
  score: number;
  reasons: string[];
}

export interface SettlementEvent {
  task_id: string;
  event_type: string;
  amount_usdc: number;
  timestamp: string;
  metadata: Record<string, string>;
}
