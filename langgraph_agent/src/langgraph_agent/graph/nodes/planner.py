"""Planner node: turns user query into an ordered list of steps."""

import re

from langchain_core.messages import HumanMessage, SystemMessage

from langgraph_agent.core import PlanExecuteState
from langgraph_agent.prompts import PLANNER_SYSTEM


def parse_plan(text: str) -> list[str]:
    """Parse LLM output into a list of step strings."""
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    steps = []
    for ln in lines:
        step = re.sub(r"^\s*\d+[.)]\s*", "", ln)
        step = re.sub(r"^\s*[-*]\s*", "", step)
        if step:
            steps.append(step)
    return steps if steps else [text.strip()]


def planner_node(state: PlanExecuteState, *, llm) -> dict:
    """Produce a plan from the user query and reset execution state."""
    query = state["query"]
    resp = llm.invoke(
        [
            SystemMessage(content=PLANNER_SYSTEM),
            HumanMessage(content=f"User goal: {query}"),
        ]
    )
    content = resp.content if hasattr(resp, "content") else str(resp)
    plan = parse_plan(content)
    return {
        "plan": plan,
        "step_index": 0,
        "step_results": [],
    }
