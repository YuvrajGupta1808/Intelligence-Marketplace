"use client";

import { FormEvent, useState } from "react";

import { createJob } from "../lib/api";


export function JobForm({ onCreated }: { onCreated: (jobId: string) => void }) {
  const [goal, setGoal] = useState("Compare pricing pages for 3 vendors.");
  const [urls, setUrls] = useState(
    "https://example.com/pricing\nhttps://openai.com/pricing\nhttps://vercel.com/pricing",
  );
  const [budget, setBudget] = useState("1.0");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const payload = await createJob(
      goal,
      urls.split("\n").map((url) => url.trim()).filter(Boolean),
      Number(budget),
    );
    onCreated(payload.job_id);
  }

  return (
    <form onSubmit={handleSubmit}>
      <label>
        Goal
        <input value={goal} onChange={(event) => setGoal(event.target.value)} />
      </label>
      <label>
        Target URLs
        <textarea rows={7} value={urls} onChange={(event) => setUrls(event.target.value)} />
      </label>
      <label>
        Max budget (USDC)
        <input value={budget} onChange={(event) => setBudget(event.target.value)} />
      </label>
      <button type="submit">Create Job</button>
    </form>
  );
}

