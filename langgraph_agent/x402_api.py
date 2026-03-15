"""
x402-compatible HTTP API for agent-to-agent commerce.

POST /run with body {"query": "..."}:
- If no payment proof: returns 402 Payment Required with amount, recipient, and how to pay.
- If Payment-Signature header (and optional X-Quote-Lamports): verifies payment on-chain, runs the agent, returns result.

Run: from repo root, cd langgraph_agent && pip install -e . && uvicorn x402_api:app --host 0.0.0.0 --port 8000
Or: python -m uvicorn langgraph_agent.x402_api:app (with PYTHONPATH including langgraph_agent)
"""

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

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from langgraph_agent import create_plan_execute_graph
from langgraph_agent.core.config import get_agent_payment_receiver, get_solana_rpc_url
from langgraph_agent.core.pricing import lamports_to_sol
from langgraph_agent.solana.payments import receiver_balance_lamports

app = FastAPI(
    title="Research Agent x402 API",
    description="Agent-to-agent commerce: POST /run with query; pay when receiving 402, then retry with Payment-Signature.",
)

# Allow common dev origins so the Next.js app can reach the API from any host/port
_cors_origins = os.getenv("X402_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://0.0.0.0:3000").strip().split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class RunBody(BaseModel):
    query: str


def _network() -> str:
    rpc = get_solana_rpc_url() or ""
    return "devnet" if "devnet" in rpc.lower() else "mainnet"


@app.post("/run")
def run(
    body: RunBody,
    payment_signature: str | None = Header(None, alias="Payment-Signature"),
    x_quote_lamports: str | None = Header(None, alias="X-Quote-Lamports"),
):
    """Run the plan-and-execute agent. Without payment: 402 + quote. With Payment-Signature: verify and run."""
    query = (body.query or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="query is required")

    receiver = get_agent_payment_receiver()
    if not receiver:
        raise HTTPException(
            status_code=503,
            detail="Agent payment receiver not configured (SOLANA_PAY_TO / X402_PAY_TO)",
        )

    graph = create_plan_execute_graph(model=None)

    if not payment_signature:
        # Stream until we have quote; capture plan from planner chunk (same order as Streamlit)
        quote_lamports = None
        plan: list[str] = []
        for chunk in graph.stream({"query": query}, stream_mode="updates"):
            if "planner" in chunk:
                plan = chunk["planner"].get("plan") or []
            if "quote" in chunk:
                upd = chunk["quote"]
                quote_lamports = upd.get("quote_lamports") or 0
                break
        if quote_lamports is None:
            raise HTTPException(status_code=500, detail="Could not compute quote")
        # Same as Streamlit: if receiver already has enough, run the graph (no paste-signature step)
        balance = receiver_balance_lamports()
        if balance >= quote_lamports:
            final_state = None
            for state in graph.stream({"query": query}, stream_mode="values"):
                final_state = state
            if not final_state:
                raise HTTPException(status_code=500, detail="Agent run produced no state")
            return {
                "final_answer": final_state.get("final_answer") or "",
                "plan": final_state.get("plan") or [],
                "tool_call_log": final_state.get("tool_call_log") or [],
            }
        sol = lamports_to_sol(quote_lamports)
        network = _network()
        return JSONResponse(
            status_code=402,
            content={
                "error": "Payment Required",
                "message": f"Pay {sol:.6f} SOL to {receiver} (devnet). The run will continue automatically when payment is detected (no need to click Run again).",
                "quote_lamports": quote_lamports,
                "quote_sol": round(sol, 9),
                "receiver": receiver,
                "network": network,
                "how_to_pay": f"Send {sol:.6f} SOL to {receiver}",
                "plan": plan,
            },
            headers={
                "Payment-Required": f"amount={quote_lamports}; token=SOL; chain=solana-{network}; recipient={receiver}",
                "X-Quote-Lamports": str(quote_lamports),
                "X-Receiver": receiver,
            },
        )

    # Verify payment then run
    try:
        quote_lamports = int(x_quote_lamports) if x_quote_lamports else None
    except ValueError:
        quote_lamports = None
    if not quote_lamports:
        # Run planner + quote to get quote_lamports, then verify
        for chunk in graph.stream({"query": query, "payment_signature": payment_signature}, stream_mode="updates"):
            if "quote" in chunk:
                quote_lamports = chunk["quote"].get("quote_lamports") or 0
                break
        if not quote_lamports:
            raise HTTPException(status_code=400, detail="Could not determine quote; send X-Quote-Lamports header")
    from langgraph_agent.solana.payments import verify_payment_by_signature
    if not verify_payment_by_signature(payment_signature, receiver, quote_lamports):
        return JSONResponse(
            status_code=402,
            content={
                "error": "Payment verification failed",
                "message": "Transaction not found, failed, or receiver balance below quote. Pay and retry.",
            },
        )

    # Run full graph with payment_signature so wait_payment skips polling
    initial = {"query": query, "payment_signature": payment_signature}
    final_state = None
    for state in graph.stream(initial, stream_mode="values"):
        final_state = state
    if not final_state:
        raise HTTPException(status_code=500, detail="Agent run produced no state")

    return {
        "final_answer": final_state.get("final_answer") or "",
        "plan": final_state.get("plan") or [],
        "tool_call_log": final_state.get("tool_call_log") or [],
    }


@app.get("/health")
def health():
    return {"status": "ok"}
