"""Executor node: runs one plan step using available tools (currently web_search only)."""

from langchain_core.messages import HumanMessage, SystemMessage

from langgraph_agent.core import PlanExecuteState
from langgraph_agent.core.pricing import LAMPORTS_PER_STEP
from langgraph_agent.prompts import EXECUTOR_SYSTEM


def executor_node(
    state: PlanExecuteState,
    *,
    llm_with_tools,
    search_tool,
    deep_research_tool=None,
) -> dict:
    """Execute the current plan step; append result and advance step_index."""
    plan = state["plan"]
    step_index = state["step_index"]
    if step_index >= len(plan):
        return {"step_index": step_index}
    budget = state.get("budget_remaining_lamports") or 0
    if budget < LAMPORTS_PER_STEP:
        return {
            "step_results": ["[Budget exhausted; step skipped.]"],
            "step_index": step_index + 1,
        }

    current_step = plan[step_index]
    messages = [
        SystemMessage(content=EXECUTOR_SYSTEM),
        HumanMessage(
            content=(
                "Current step to execute: "
                f"{current_step}\n\n"
                "Decide which web_search query to run to best execute this step. "
                "Call exactly ONE tool once with a good input."
            )
        ),
    ]
    response = llm_with_tools.invoke(messages)
    observation = ""

    if response.tool_calls:
        for tc in response.tool_calls:
            name = tc.get("name")
            args = tc.get("args") or {}
            if name == "web_search":
                observation = search_tool.invoke(args)
                break
        if not observation and response.tool_calls:
            args = response.tool_calls[0].get("args") or {}
            # Fallback to web_search if tool name was unrecognized.
            observation = search_tool.invoke(args)
    else:
        observation = response.content if hasattr(response, "content") else str(response)

    return {
        "step_results": [observation],
        "step_index": step_index + 1,
    }
