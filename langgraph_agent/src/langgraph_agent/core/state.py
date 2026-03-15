"""State schema and reducers for the plan-and-execute graph."""

from operator import add
from typing import Annotated, Any

from typing_extensions import NotRequired, TypedDict


class PlanExecuteState(TypedDict):
    """State for the plan-and-execute agent (payment-aware)."""

    query: str
    plan: list[str]
    step_index: int
    step_results: Annotated[list[str], add]
    final_answer: str
    # Payment flow (optional until quote node runs)
    quote_lamports: NotRequired[int]
    invoice_id: NotRequired[str]
    payment_receiver: NotRequired[str]
    payment_status: NotRequired[str]
    payment_tx: NotRequired[str]
    receiver_balance_at_quote_lamports: NotRequired[int]
    budget_remaining_lamports: NotRequired[int]
    tool_call_log: NotRequired[list[dict[str, Any]]]
    agent_reasoning: NotRequired[list[str]]
