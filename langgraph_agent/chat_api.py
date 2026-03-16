"""
Simple HTTP API exposing the \"chat\" section data (plan, quote, etc.).

Run from repo root:
  cd langgraph_agent && pip install -e .
  uvicorn chat_api:app --host 0.0.0.0 --port 7000

POST /chat with body {"query": "..."} returns:
- plan: ordered list of steps from the planner
- quote_lamports / quote_sol: price for the run (if payment configured)
- receiver / network: where to pay on Solana (if configured)
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    for d in (Path(__file__).resolve().parent, Path(__file__).resolve().parents[1]):
        if (d / ".env").exists():
            load_dotenv(d / ".env")
            break
except ImportError:
    pass

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from langgraph_agent import create_plan_execute_graph
from langgraph_agent.core.config import get_agent_payment_receiver, get_solana_rpc_url
from langgraph_agent.core.pricing import lamports_to_sol


class ChatBody(BaseModel):
    query: str


app = FastAPI(
    title="Plan & Execute Chat API",
    description="Expose plan and quote data (chat section) for the LangGraph agent.",
)

_cors_origins = os.getenv(
    "CHAT_API_CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://0.0.0.0:3000",
).strip().split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


def _network() -> str:
    rpc = get_solana_rpc_url() or ""
    return "devnet" if "devnet" in rpc.lower() else "mainnet"


@app.post("/chat")
def chat(body: ChatBody):
    """
    Return the planner output (plan) and quote for the given query.

    This mirrors the \"Metaplex / quote\" portion of the Streamlit UI so that other
    frontends can render plans, prices, and payment instructions.
    """
    query = (body.query or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="query is required")

    graph = create_plan_execute_graph(model=None)

    plan: list[str] = []
    quote_lamports: int | None = None
    payment_receiver = get_agent_payment_receiver() or ""

    # Stream until we have planner and quote updates (same behavior as Streamlit).
    for chunk in graph.stream({"query": query}, stream_mode="updates"):
        if "planner" in chunk:
            plan = chunk["planner"].get("plan") or []
        if "quote" in chunk:
            upd = chunk["quote"]
            quote_lamports = upd.get("quote_lamports") or 0
            if not payment_receiver:
                payment_receiver = upd.get("payment_receiver") or ""
            break

    if quote_lamports is None:
        raise HTTPException(status_code=500, detail="Could not compute quote")

    quote_sol = lamports_to_sol(quote_lamports)
    network = _network()

    return {
        "query": query,
        "plan": plan,
        "quote_lamports": quote_lamports,
        "quote_sol": quote_sol,
        "receiver": payment_receiver,
        "network": network,
        "how_to_pay": (
            f"Send {quote_sol:.6f} SOL to {payment_receiver} on solana-{network}"
            if payment_receiver
            else ""
        ),
    }


@app.get("/health")
def health():
    return {"status": "ok"}


def _sse_event(event: str, data: str) -> str:
    """Format a Server-Sent Event line."""
    return f"event: {event}\ndata: {data}\n\n"


@app.post("/chat/stream")
def chat_stream(body: ChatBody):
    """
    Stream planner, quote, execution steps, and final answer as Server-Sent Events.

    Frontends can listen with EventSource and will receive events:
    - planner: { "plan": [...] }
    - quote: { "quote_lamports": ..., "quote_sol": ..., "receiver": ..., "network": ... }
    - step: { "step_index": n, "result": "..." }
    - final_answer: { "final_answer": "..." }
    - done: {}
    """

    query = (body.query or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="query is required")

    graph = create_plan_execute_graph(model=None)
    explorer_network = _network()

    def event_generator():
        # First, stream structured node updates like the Streamlit app.
        for chunk in graph.stream({"query": query}, stream_mode="updates"):
            import json as _json
            if "planner" in chunk:
                plan = chunk["planner"].get("plan") or []
                payload = {"plan": plan}
                yield _sse_event("planner", _json.dumps(payload))
            if "quote" in chunk:
                upd = chunk["quote"]
                q_lamports = upd.get("quote_lamports") or 0
                receiver = upd.get("payment_receiver") or (get_agent_payment_receiver() or "")
                q_sol = lamports_to_sol(q_lamports)
                payload = {
                    "quote_lamports": q_lamports,
                    "quote_sol": q_sol,
                    "receiver": receiver,
                    "network": explorer_network,
                }
                yield _sse_event("quote", _json.dumps(payload))

        # Then stream the values view to surface step results and final answer.
        last_step_index = -1
        for state in graph.stream({"query": query}, stream_mode="values"):
            plan = state.get("plan") or []
            step_results = state.get("step_results") or []
            if plan and step_results:
                # Emit any new step result.
                if len(step_results) - 1 > last_step_index:
                    last_step_index = len(step_results) - 1
                    step_payload = {
                        "step_index": last_step_index,
                        "result": step_results[last_step_index],
                    }
                    import json as _json

                    yield _sse_event("step", _json.dumps(step_payload))

            final_answer = state.get("final_answer")
            if final_answer:
                import json as _json

                yield _sse_event(
                    "final_answer",
                    _json.dumps({"final_answer": final_answer}),
                )

            # Emit tool payments (on-chain) when we have them (same state as final_answer).
            tool_call_log = state.get("tool_call_log") or []
            if tool_call_log:
                import json as _json

                yield _sse_event(
                    "tool_payments",
                    _json.dumps({"tool_call_log": tool_call_log}),
                )

        # Signal completion.
        yield _sse_event("done", "{}")

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/chat/stream-get")
def chat_stream_get(query: str = Query(..., min_length=1)):
    """
    GET variant of chat_stream for EventSource clients that can only use GET.
    """
    body = ChatBody(query=query)
    return chat_stream(body)


