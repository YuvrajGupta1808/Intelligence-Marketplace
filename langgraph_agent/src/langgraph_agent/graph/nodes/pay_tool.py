"""Pay-tool node: deduct step cost from budget and send real payout to tool provider."""

from langgraph_agent.core import PlanExecuteState
from langgraph_agent.core.config import get_tool_payout_address
from langgraph_agent.core.pricing import LAMPORTS_PER_STEP
from langgraph_agent.solana.payments import send_lamports_to_tool_provider


def pay_tool_node(state: PlanExecuteState) -> dict:
    """After a step, deduct cost, send lamports to tool payout address if configured, and log."""
    budget = state.get("budget_remaining_lamports") or 0
    log = list(state.get("tool_call_log") or [])
    cost = min(LAMPORTS_PER_STEP, budget)
    to_address = get_tool_payout_address()
    if to_address and cost > 0:
        tx_sig = send_lamports_to_tool_provider(to_address, cost)
        tx = tx_sig if tx_sig else "failed"
    else:
        tx = "simulated"
    log.append({
        "tool": "web_search",
        "amount_lamports": cost,
        "tx": tx,
    })
    return {
        "tool_call_log": log,
        "budget_remaining_lamports": budget - cost,
    }