from __future__ import annotations

import json
from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.models.schemas import TaskPayload


@dataclass
class PlannerPlan:
    rationale_summary: str
    decision_log: list[str]
    selected_workers: list[str]
    execution_order: list[str]
    settlement_policy: str
    provider: str


class DeterministicPlanner:
    async def generate_plan(self, goal: str, tasks: list[TaskPayload], max_budget_usdc: float) -> PlannerPlan:
        worker_id = "unbrowse-browser-agent" if settings.payment_mode == "real" else "browser-1"
        return PlannerPlan(
            rationale_summary=(
                f"Interpret goal '{goal}' as deterministic pricing extraction across {len(tasks)} provided URLs "
                f"within a maximum budget of {max_budget_usdc:.2f} USDC."
            ),
            decision_log=[
                "Used deterministic planner fallback because no OpenAI planner credentials were configured.",
                "Accepted the explicit URL list instead of autonomous discovery.",
                f"Selected {worker_id} as the active worker runtime.",
                "Will run quote, x402 payment retry, browse, verify, and settle in sequence.",
            ],
            selected_workers=[worker_id],
            execution_order=[task.id for task in tasks],
            settlement_policy="Release only when deterministic verification passes; otherwise refund.",
            provider="deterministic",
        )


class OpenAIPlanner:
    async def generate_plan(self, goal: str, tasks: list[TaskPayload], max_budget_usdc: float) -> PlannerPlan:
        worker_id = "unbrowse-browser-agent" if settings.payment_mode == "real" else "browser-1"
        prompt_tasks = [
            {
                "task_id": task.id,
                "target_url": task.target_url,
                "allowed_domain": task.allowed_domain,
                "required_fields": task.required_fields,
                "deadline_seconds": task.deadline_seconds,
            }
            for task in tasks
        ]
        body = {
            "model": settings.openai_model,
            "reasoning": {"effort": settings.openai_reasoning_effort},
            "instructions": (
                "You are the planner for a paid browser automation system. "
                "Return strict JSON only. Do not include markdown fences. "
                f"Keep the plan deterministic, use only the supplied URLs, use {worker_id} as the worker, "
                "and ensure settlement releases only on verification pass."
            ),
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": json.dumps(
                                {
                                    "goal": goal,
                                    "max_budget_usdc": max_budget_usdc,
                                    "tasks": prompt_tasks,
                                    "required_response_shape": {
                                        "rationale_summary": "string",
                                        "decision_log": ["string"],
                                        "selected_workers": [worker_id],
                                        "execution_order": ["task_id"],
                                        "settlement_policy": "string",
                                    },
                                }
                            ),
                        }
                    ],
                }
            ],
        }
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=settings.openai_timeout_sec) as client:
            response = await client.post(f"{settings.openai_base_url}/responses", json=body, headers=headers)
            response.raise_for_status()
        payload = response.json()
        output_text = payload.get("output_text", "").strip()
        if not output_text:
            raise ValueError("OpenAI planner returned no text output")
        plan_json = json.loads(output_text)
        execution_order = [task_id for task_id in plan_json.get("execution_order", []) if task_id in {task.id for task in tasks}]
        missing = [task.id for task in tasks if task.id not in execution_order]
        decision_log = [str(item) for item in plan_json.get("decision_log", []) if str(item).strip()]
        return PlannerPlan(
            rationale_summary=str(plan_json.get("rationale_summary") or "Generated plan from OpenAI Responses API."),
            decision_log=decision_log or ["Received planner output from OpenAI Responses API."],
            selected_workers=[str(item) for item in plan_json.get("selected_workers", []) if str(item).strip()] or [worker_id],
            execution_order=execution_order + missing,
            settlement_policy=str(
                plan_json.get("settlement_policy")
                or "Release only when deterministic verification passes; otherwise refund."
            ),
            provider="openai",
        )


class PlannerService:
    def __init__(self) -> None:
        self.provider = settings.planner_provider.lower()
        provider = self.provider
        if provider == "openai" or (provider == "auto" and settings.openai_api_key):
            self.impl = OpenAIPlanner()
        else:
            self.impl = DeterministicPlanner()

    async def generate_plan(self, goal: str, tasks: list[TaskPayload], max_budget_usdc: float) -> PlannerPlan:
        try:
            return await self.impl.generate_plan(goal, tasks, max_budget_usdc)
        except Exception:
            if self.provider != "auto" or settings.real_mode():
                raise
            fallback = DeterministicPlanner()
            plan = await fallback.generate_plan(goal, tasks, max_budget_usdc)
            plan.decision_log.append("OpenAI planner failed, so the planner fell back to the deterministic local policy.")
            return plan
