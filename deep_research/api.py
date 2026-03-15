"""
FastAPI app exposing the deep finance research agent for testing and API access.

Endpoints:
  GET  /health       - Liveness
  POST /research_report - Run research for a query/ticker and return the report.

Run: uv run uvicorn deep_research.api:app --reload --port 8000
"""
from __future__ import annotations

import json
import os
import uuid
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

load_dotenv()


def _get_agent():
    """Lazy-load the agent so env is loaded and startup is fast."""
    from deep_research.agent import agent
    return agent


def _run_research(agent, query: str, thread_id: str) -> tuple[str, list[str], list[str]]:
    """Run the agent and return (report_text, tools_used, chart_jsons)."""
    from pathlib import Path

    from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

    from deep_research.config import PROJECT_ROOT

    config = {"configurable": {"thread_id": thread_id, "user_id": "api-user"}}
    state = {
        "messages": [HumanMessage(content=query)],
        "thread_id": thread_id,
        "user_id": "api-user",
    }

    full_response = ""
    tool_calls_list = []
    tool_call_id_to_name = {}
    chart_jsons = []
    task_report = ""
    final_report_path = PROJECT_ROOT / "output" / "final_report.md"
    final_report_path.parent.mkdir(parents=True, exist_ok=True)

    def _write_final_report(content: str) -> None:
        if content and len(content) > 300:
            try:
                final_report_path.write_text(content, encoding="utf-8")
            except OSError:
                pass

    for chunk in agent.stream(state, stream_mode="messages", config=config):
        message = chunk[0] if isinstance(chunk, tuple) else chunk

        if isinstance(message, AIMessage) and message.tool_calls:
            for tool_call in message.tool_calls:
                name = tool_call.get("name", "?")
                tid = tool_call.get("id") or tool_call.get("tool_call_id")
                if tid:
                    tool_call_id_to_name[tid] = name
                tool_calls_list.append(name)

        elif isinstance(message, ToolMessage):
            content = getattr(message, "content", None) or ""
            tid = getattr(message, "tool_call_id", None)
            name = tool_call_id_to_name.get(tid, "") if tid else ""
            if name == "generate_price_chart" and content:
                try:
                    json.loads(content)
                    chart_jsons.append(content)
                except (TypeError, json.JSONDecodeError):
                    pass
            if content and len(content) > 400 and ("## " in content or "### " in content):
                task_report = content
                _write_final_report(task_report)

        elif isinstance(message, AIMessage) and message.content:
            full_response += message.content
            _write_final_report(full_response)

    display_content = (
        full_response
        if (full_response and len(full_response) > len(task_report))
        else (task_report if task_report else full_response)
    )
    _write_final_report(display_content)
    return display_content, tool_calls_list, chart_jsons


class ResearchReportRequest(BaseModel):
    """Request body for POST /research_report."""

    query: str = Field(..., min_length=1, description="Research query, e.g. 'Research AAPL' or 'Full company report on Microsoft'.")
    thread_id: str | None = Field(None, description="Optional thread ID for conversation continuity.")


class ResearchReportResponse(BaseModel):
    """Response for POST /research_report."""

    report: str = Field(..., description="Full research report (markdown).")
    tools_used: list[str] = Field(default_factory=list, description="Tool names invoked.")
    chart_count: int = Field(0, description="Number of price charts generated.")
    thread_id: str = Field(..., description="Thread ID used for this run.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Optional: validate Unbrowse on startup."""
    yield


app = FastAPI(
    title="Deep Finance Research API",
    description="Run the deep finance research agent and get CFA-style reports.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check."""
    return {"status": "ok"}


@app.post("/research_report", response_model=ResearchReportResponse)
def research_report(body: ResearchReportRequest) -> ResearchReportResponse:
    """
    Run the research agent for the given query and return the full report.

    Use this endpoint to test the final outcome of the research pipeline.
    Requires FIREWORKS_API_KEY and (for full research) Unbrowse server.
    """
    thread_id = body.thread_id or str(uuid.uuid4())
    if not os.getenv("FIREWORKS_API_KEY", "").strip():
        raise HTTPException(
            status_code=503,
            detail="FIREWORKS_API_KEY not set. Configure .env to run research.",
        )
    try:
        agent = _get_agent()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Agent failed to load: {e!s}")

    try:
        report_text, tools_used, chart_jsons = _run_research(agent, body.query, thread_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Research run failed: {e!s}")

    return ResearchReportResponse(
        report=report_text,
        tools_used=tools_used,
        chart_count=len(chart_jsons),
        thread_id=thread_id,
    )
