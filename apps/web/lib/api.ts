const plannerBase = process.env.NEXT_PUBLIC_PLANNER_API_URL ?? "http://localhost:8001";

export async function createJob(goal: string, urls: string[], maxBudget: number) {
  const response = await fetch(`${plannerBase}/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ goal, target_urls: urls, max_budget_usdc: maxBudget }),
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Failed to create job");
  }
  return response.json();
}

export async function runJob(jobId: string) {
  const response = await fetch(`${plannerBase}/jobs/${jobId}/run`, {
    method: "POST",
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Failed to run job");
  }
  return response.json();
}

export async function getJob(jobId: string) {
  const response = await fetch(`${plannerBase}/jobs/${jobId}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Failed to fetch job");
  }
  return response.json();
}

