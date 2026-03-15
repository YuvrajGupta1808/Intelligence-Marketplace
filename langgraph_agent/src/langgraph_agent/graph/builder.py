"""Plan-and-execute graph: planner -> quote -> wait_payment -> executor (pay_tool loop) -> synthesize."""

from typing import Literal

from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from langgraph_agent.core import (
    PlanExecuteState,
    get_agent_payment_receiver,
    get_model,
    get_temperature,
)
from langgraph_agent.graph.nodes import (
    executor_node,
    pay_tool_node,
    planner_node,
    quote_node,
    synthesize_node,
    wait_payment_node,
)
from langgraph_agent.tools import get_search_tool


def _create_llm(model: str | None = None, temperature: float | None = None):
    return ChatOpenAI(
        model=model or get_model(),
        temperature=temperature if temperature is not None else get_temperature(),
    )


def _after_wait_payment(state: PlanExecuteState) -> Literal["executor", "end"]:
    if state.get("payment_status") == "confirmed":
        return "executor"
    return "end"


def _after_pay_tool(state: PlanExecuteState) -> Literal["executor", "synthesize"]:
    if state["step_index"] >= len(state["plan"]):
        return "synthesize"
    return "executor"


def create_plan_execute_graph(model: str | None = None):
    """Build and compile the plan-and-execute graph with quote/payment gating."""
    llm = _create_llm(model)
    search_tool = get_search_tool()
    llm_with_tools = llm.bind_tools([search_tool])
    receiver = get_agent_payment_receiver() or ""

    def planner(state: PlanExecuteState) -> dict:
        return planner_node(state, llm=llm)

    def quote(state: PlanExecuteState) -> dict:
        return quote_node(state, payment_receiver=receiver)

    def executor(state: PlanExecuteState) -> dict:
        return executor_node(
            state,
            llm_with_tools=llm_with_tools,
            search_tool=search_tool,
        )

    def synthesize(state: PlanExecuteState) -> dict:
        return synthesize_node(state, llm=llm)

    builder = StateGraph(PlanExecuteState)
    builder.add_node("planner", planner)
    builder.add_node("quote", quote)
    builder.add_node("wait_payment", wait_payment_node)
    builder.add_node("executor", executor)
    builder.add_node("pay_tool", pay_tool_node)
    builder.add_node("synthesize", synthesize)
    builder.add_edge(START, "planner")
    builder.add_edge("planner", "quote")
    builder.add_edge("quote", "wait_payment")
    builder.add_conditional_edges(
        "wait_payment",
        _after_wait_payment,
        {"executor": "executor", "end": END},
    )
    builder.add_edge("executor", "pay_tool")
    builder.add_conditional_edges(
        "pay_tool",
        _after_pay_tool,
        {"executor": "executor", "synthesize": "synthesize"},
    )
    builder.add_edge("synthesize", END)

    return builder.compile()
