"use client";

import { useEffect, useState, useTransition } from "react";

import { JobForm } from "../components/JobForm";
import { PlannerTrace } from "../components/PlannerTrace";
import { SponsorPanels } from "../components/SponsorPanels";
import { StatusBadge } from "../components/StatusBadge";
import { TaskBoard } from "../components/TaskBoard";
import { Timeline } from "../components/Timeline";
import { getJob, runJob } from "../lib/api";


export default function Page() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [job, setJob] = useState<any | null>(null);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    if (!jobId) return;
    const currentJobId = jobId;
    let active = true;

    async function load() {
      const nextJob = await getJob(currentJobId);
      if (active) setJob(nextJob);
    }

    void load();
    const interval = setInterval(load, 3000);
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [jobId]);

  async function handleRun() {
    if (!jobId) return;
    startTransition(async () => {
      await runJob(jobId);
      setJob(await getJob(jobId));
    });
  }

  return (
    <main>
      <div className="shell">
        <section className="hero">
          <StatusBadge label="proof-of-browse" />
          <h1>Paid browser labor, verified before settlement.</h1>
          <p>
            Proof-of-Browse is a multi-agent app for paid web work. A planner agent decides how to run a job, a browser
            worker performs the task, a verifier checks the evidence, and the payment layer records whether funds should
            be released or refunded.
          </p>
        </section>

        <section className="three-column">
          <section className="panel">
            <h2>What This App Is</h2>
            <p>
              This app orchestrates browser tasks as a visible workflow. It is designed to show how agents can plan,
              execute, verify, and settle paid web work instead of hiding those steps inside a black box.
            </p>
          </section>

          <section className="panel">
            <h2>What Problem It Solves</h2>
            <p>
              Most agent demos do not show who did the work, what proof came back, or how money moved. This app makes
              the planner decision, browser evidence, verification outcome, and settlement timeline inspectable.
            </p>
          </section>

          <section className="panel">
            <h2>Agent Roles</h2>
            <div className="info-list">
              <p><strong>Planner</strong>: decomposes the goal and runs the workflow.</p>
              <p><strong>Browser worker</strong>: performs the paid web task.</p>
              <p><strong>Verifier</strong>: applies deterministic pass/fail rules.</p>
              <p><strong>Settlement layer</strong>: records funded, released, or refunded outcomes.</p>
            </div>
          </section>
        </section>

        <section className="two-column">
          <section className="panel">
            <h2>How To Use It</h2>
            <ol className="flow-list">
              <li>Create a job with a goal, URLs, and a budget.</li>
              <li>Click <strong>Run Job</strong>.</li>
              <li>Watch the workflow panel, planner trace, and settlement timeline update.</li>
              <li>Open Temporal UI to inspect the same workflow at the activity level.</li>
            </ol>
          </section>

          <section className="panel">
            <h2>Platforms In Use</h2>
            <div className="info-list">
              <p><strong>Frontend</strong>: Next.js and React</p>
              <p><strong>Planner API</strong>: FastAPI, SQLAlchemy, Temporal Python SDK</p>
              <p><strong>Browser worker</strong>: FastAPI, Playwright, Unbrowse integration</p>
              <p><strong>Workflow engine</strong>: Temporal</p>
              <p><strong>Payment runtime</strong>: x402 on Solana devnet</p>
              <p><strong>Escrow runtime</strong>: Alkahest on Base Sepolia</p>
            </div>
          </section>
        </section>

        <section className="panel">
          <h2>What Happens During A Run</h2>
          <ol className="flow-list">
            <li>The planner API creates a job and task records.</li>
            <li>Temporal starts a workflow for the job.</li>
            <li>The planner generates an execution plan.</li>
            <li>The browser worker returns a quote.</li>
            <li>The settlement layer records funding.</li>
            <li>The paid browse call runs through the sponsor runtime.</li>
            <li>The browser worker returns structured evidence.</li>
            <li>The verifier checks the evidence.</li>
            <li>The app records release or refund settlement.</li>
          </ol>
        </section>

        <div className="grid">
          <section className="panel">
            <h2>Create Job</h2>
            <JobForm onCreated={setJobId} />
            {jobId ? <p>Current job: {jobId}</p> : null}
            <button onClick={handleRun} disabled={!jobId || isPending}>
              {isPending ? "Running..." : "Run Job"}
            </button>
          </section>

          <section className="panel">
            <h2>Job Detail</h2>
            {job ? (
              <>
                <div className="meta">
                  <StatusBadge label={job.job.status} />
                  <span>Budget: {job.job.max_budget_usdc} USDC</span>
                </div>
                <p>{job.job.goal}</p>
                <TaskBoard job={job} />
              </>
            ) : (
              <p>Create a job to start the task board.</p>
            )}
          </section>
        </div>

        <section className="panel">
          <h2>Settlement Timeline</h2>
          {job ? <Timeline events={job.settlement_events} /> : <p>No settlement events yet.</p>}
        </section>

        {job ? <SponsorPanels job={job} /> : null}

        {job ? (
          <section className="panel">
            <h2>Workflow Execution</h2>
            <div className="meta">
              <StatusBadge label={job.workflow.workflow_status} />
              <StatusBadge label={job.workflow.current_activity} />
            </div>
            <p>Workflow ID: {job.workflow.workflow_id ?? "not started"}</p>
            <p>Run ID: {job.workflow.run_id ?? "pending"}</p>
            <p>
              Namespace: {job.workflow.namespace} · Task queue: {job.workflow.task_queue}
            </p>
            {job.workflow.temporal_ui_url ? (
              <p>
                Temporal UI:{" "}
                <a href={job.workflow.temporal_ui_url} target="_blank" rel="noreferrer">
                  {job.workflow.temporal_ui_url}
                </a>
              </p>
            ) : null}
          </section>
        ) : null}

        {job ? (
          <section className="two-column">
            <PlannerTrace plannerRun={job.planner_run} traceEvents={job.trace_events} />
            <section className="panel">
              <h2>Planner Summary</h2>
              <div className="meta">
                <StatusBadge label={job.planner_run.planner_status} />
                <StatusBadge label={job.planner_run.current_step} />
              </div>
              <p>{job.planner_run.rationale_summary}</p>
              <p>Workflow activity: {job.planner_run.current_activity}</p>
              <p>Selected workers: {job.planner_run.selected_workers.join(", ") || "none"}</p>
            </section>
          </section>
        ) : null}
      </div>
    </main>
  );
}
