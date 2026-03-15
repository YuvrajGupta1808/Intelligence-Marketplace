"""Wait payment node: poll until user payment is seen on-chain, then proceed."""

import time

from langgraph_agent.core import PlanExecuteState
from langgraph_agent.core.config import (
    get_payment_poll_interval_sec,
    get_payment_poll_max_wait_sec,
)
from langgraph_agent.solana.payments import check_payment_received


def wait_payment_node(state: PlanExecuteState) -> dict:
    """Poll receiver balance until payment >= quote or timeout; then set confirmed or pending."""
    quote = state.get("quote_lamports") or 0
    start_bal = state.get("receiver_balance_at_quote_lamports") or 0
    if quote <= 0:
        return {"payment_status": "confirmed"}
    if check_payment_received(start_bal, quote):
        return {
            "payment_status": "confirmed",
            "budget_remaining_lamports": quote,
        }
    interval = get_payment_poll_interval_sec()
    max_wait = get_payment_poll_max_wait_sec()
    deadline = time.monotonic() + max_wait
    while time.monotonic() < deadline:
        time.sleep(interval)
        if check_payment_received(start_bal, quote):
            return {
                "payment_status": "confirmed",
                "budget_remaining_lamports": quote,
            }
    return {"payment_status": "pending"}