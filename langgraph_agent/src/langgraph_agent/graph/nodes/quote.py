"""Quote node: set price (lamports) and receiver; record receiver balance for verification."""

import uuid

from langgraph_agent.core import PlanExecuteState
from langgraph_agent.core.pricing import compute_quote_lamports
from langgraph_agent.solana.payments import receiver_balance_lamports


def quote_node(state: PlanExecuteState, *, payment_receiver: str) -> dict:
    """Set quote_lamports, invoice_id, payment_receiver; snapshot receiver balance."""
    plan = state["plan"]
    num_steps = max(1, len(plan))
    if not payment_receiver:
        return {
            "quote_lamports": 0,
            "invoice_id": str(uuid.uuid4()),
            "payment_receiver": "",
            "payment_status": "confirmed",
            "receiver_balance_at_quote_lamports": 0,
            "budget_remaining_lamports": 10**15,
            "tool_call_log": [],
        }
    quote_lamports = compute_quote_lamports(num_steps)
    balance_now = receiver_balance_lamports()
    return {
        "quote_lamports": quote_lamports,
        "invoice_id": str(uuid.uuid4()),
        "payment_receiver": payment_receiver,
        "payment_status": "pending",
        "receiver_balance_at_quote_lamports": balance_now,
        "budget_remaining_lamports": 0,
        "tool_call_log": [],
    }