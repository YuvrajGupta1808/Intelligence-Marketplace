"""Synthesizer node: produces final answer from plan and step results."""

from langchain_core.messages import HumanMessage, SystemMessage

from langgraph_agent.core import PlanExecuteState
from langgraph_agent.prompts import SYNTHESIZE_SYSTEM


def synthesize_node(state: PlanExecuteState, *, llm) -> dict:
    """Synthesize a final answer from the query, plan, and step results."""
    query = state["query"]
    plan = state["plan"]
    results = state.get("step_results") or []
    context = "\n\n".join(
        [f"Step {i+1}: {p}\nResult: {r}" for i, (p, r) in enumerate(zip(plan, results))]
    )
    resp = llm.invoke(
        [
            SystemMessage(content=SYNTHESIZE_SYSTEM),
            HumanMessage(
                content=f"User goal: {query}\n\nPlan and results:\n{context}\n\nWrite the final answer."
            ),
        ]
    )
    answer = resp.content if hasattr(resp, "content") else str(resp)
    log = state.get("tool_call_log") or []
    if log:
        total = sum(e.get("amount_lamports", 0) for e in log)
    return {"final_answer": answer}
