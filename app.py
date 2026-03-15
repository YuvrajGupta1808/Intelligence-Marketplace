"""
Basic Streamlit app to preview the deep finance research agent.
Run from project root: uv run streamlit run app.py
"""
import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import json
import os
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# Load env before importing agent
from dotenv import load_dotenv
load_dotenv()


# Map tool names to API/source for the activity panel
TOOL_TO_API = {
    "task": "Sub-agent delegation",
    "live_finance_researcher": "Yahoo Finance",
    "generate_price_chart": "Yahoo Finance (yfinance)",
    "think_tool": "Internal",
    "list_skills": "Internal",
    "load_skill": "Internal",
    "generate_research_pdf": "Internal (PDF)",
}
# Prefix-based for unbrowse and exa
for t in ("unbrowse_health", "unbrowse_resolve", "unbrowse_execute", "unbrowse_feedback",
          "unbrowse_search", "unbrowse_search_domain", "unbrowse_list_skills", "unbrowse_skill_detail",
          "register_unbrowse_skill", "get_unbrowse_registry"):
    TOOL_TO_API[t] = "Unbrowse (SEC.gov / web)"
for t in ("exa_web_search", "exa_get_contents"):
    TOOL_TO_API[t] = "EXA (web search)"


def _tool_api(tool_name: str) -> str:
    return TOOL_TO_API.get(tool_name) or "—"


def _task_subagent_from_args(args: dict) -> str | None:
    """Extract sub-agent name from task() tool args if present."""
    if not args:
        return None
    for key in ("subagent_type", "agent", "sub_agent", "name", "agent_name"):
        v = args.get(key)
        if isinstance(v, str) and v and ("agent" in v or "-" in v):
            return v
    return None


def _args_preview(args: dict, tool_name: str, max_len: int = 60) -> str:
    """Short preview of tool args for display."""
    if not args or not isinstance(args, dict):
        return ""
    if tool_name == "task":
        # Show task description snippet
        desc = args.get("task", args.get("message", args.get("input", "")))
        if isinstance(desc, str) and desc:
            return (desc.strip()[:max_len] + "…") if len(desc) > max_len else desc.strip()
    if tool_name == "generate_price_chart":
        t = args.get("ticker", "")
        p = args.get("period", "")
        return f"ticker={t}, period={p}" if t else ""
    if tool_name == "live_finance_researcher":
        q = args.get("query", "")[:max_len]
        return f'"{q}…"' if len(str(args.get("query", ""))) > max_len else f'"{q}"'
    return ""


def get_agent():
    """Lazy-load the agent to avoid slow startup and allow env to be loaded."""
    from deep_research.agent import agent
    return agent


def render_activity_panel(activity_entries: list, placeholder) -> None:
    """Write current activity log into the placeholder (tools, agents, APIs)."""
    if not activity_entries:
        placeholder.markdown("*No activity yet.*")
        return
    lines = []
    for i, e in enumerate(activity_entries, 1):
        tool = e.get("tool", "?")
        api = e.get("api", "—")
        sub = e.get("sub_agent")
        preview = e.get("args_preview", "")
        if sub:
            lines.append(f"{i}. **{tool}** → **{sub}**  \n   API: *{api}*")
        else:
            lines.append(f"{i}. **{tool}**  \n   API: *{api}*")
        if preview:
            lines.append(f"   `{preview}`")
    placeholder.markdown("\n\n".join(lines))


def stream_agent_into_ui(agent, query: str, thread_id: str, message_placeholder, activity_placeholder=None):
    """Stream agent response into a Streamlit placeholder. Returns (display_content, tool_calls_list, chart_jsons, activity_entries).
    When the agent delegates with task(), the full report is in the task tool result; we capture and show it.
    If activity_placeholder is provided, live tool calls and API usage are written there.
    """
    config = {"configurable": {"thread_id": thread_id, "user_id": "streamlit-user"}}
    state = {
        "messages": [HumanMessage(content=query)],
        "thread_id": thread_id,
        "user_id": "streamlit-user",
    }

    full_response = ""
    tool_calls_list = []
    tool_call_id_to_name = {}
    chart_jsons = []
    task_report = ""
    activity_entries = []

    for chunk in agent.stream(state, stream_mode="messages", config=config):
        message = chunk[0] if isinstance(chunk, tuple) else chunk

        if isinstance(message, AIMessage) and message.tool_calls:
            for tool_call in message.tool_calls:
                name = tool_call.get("name", "?")
                args = tool_call.get("args") or {}
                tid = tool_call.get("id") or tool_call.get("tool_call_id")
                if tid:
                    tool_call_id_to_name[tid] = name
                tool_calls_list.append(f"**{name}**")

                sub_agent = _task_subagent_from_args(args) if name == "task" else None
                activity_entries.append({
                    "tool": name,
                    "api": _tool_api(name),
                    "sub_agent": sub_agent,
                    "args_preview": _args_preview(args, name),
                })
                if activity_placeholder is not None:
                    render_activity_panel(activity_entries, activity_placeholder)

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
                message_placeholder.markdown(task_report + "▌")

        elif isinstance(message, AIMessage) and message.content:
            full_response += message.content
            if not task_report:
                message_placeholder.markdown(full_response + "▌")

    display_content = (
        full_response
        if (full_response and len(full_response) > len(task_report))
        else (task_report if task_report else full_response)
    )
    message_placeholder.markdown(display_content)
    return display_content, tool_calls_list, chart_jsons, activity_entries


st.set_page_config(page_title="Deep Finance Research", page_icon="📊", layout="centered")
st.title("📊 Deep Finance Research Agent")
st.caption(
    "Investor-ready **17-section CFA-style reports** from **Yahoo Finance**, **EXA** (web search), and **Unbrowse** (SEC.gov and the web). "
    "Three sub-agents divide research; the orchestrator synthesizes. Try: *\"Research Microsoft\"* or *\"Full company report on NVIDIA\"*."
)

with st.sidebar:
    st.caption("Set `FIREWORKS_API_KEY` in `.env` to use the agent. Optional: `EXA_API_KEY` for web search.")
    # Unbrowse health: warn if down so first chat doesn't fail with a generic error
    try:
        import requests
        unbrowse_url = os.getenv("UNBROWSE_URL", "http://localhost:6969").rstrip("/")
        r = requests.get(f"{unbrowse_url}/health", timeout=2)
        if r.status_code != 200:
            st.warning("Unbrowse returned non-200. Start with: `unbrowse setup`")
    except Exception:
        st.warning("Unbrowse not reachable. Start with: `unbrowse setup` (required for research).")
    # EXA config status
    if os.getenv("EXA_API_KEY", "").strip():
        st.caption("EXA web search: configured.")
    else:
        st.caption("EXA: not set (add EXA_API_KEY in .env for web search).")
    st.divider()

    with st.expander("**Workflow**", expanded=True):
        st.markdown(
            """
            1. **You ask** for a company or ticker (e.g. *Research AAPL*).
            2. **Orchestrator** plans and delegates to three sub-agents:
               - **company-data-agent** — Header, business description, historical financials (Yahoo, Unbrowse/SEC).
               - **industry-competitors-agent** — Industry overview, competitors, moat (EXA, Unbrowse).
               - **valuation-risks-agent** — Valuation, recommendation, risks, catalysts (Yahoo, EXA, Unbrowse).
            3. **Unbrowse** skills are created on first use and reused by other agents (same URL). To see Unbrowse-created skills, ask the agent: *List Unbrowse skills*.
            4. **Orchestrator** merges the three outputs into one **17-section report** (CFA/FINRA-style).
            5. Report is shown here; a **PDF** is generated at the end and saved under output/ (via the deep-research-pdf skill).
            """
        )
    st.divider()

    if st.button("New conversation"):
        import uuid
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    import uuid
    st.session_state.thread_id = str(uuid.uuid4())

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        for cj in msg.get("charts") or []:
            try:
                import plotly.io as pio
                fig = pio.from_json(cj)
                st.plotly_chart(fig, use_container_width=True)
            except Exception:
                pass
        # Show tools, agents, and APIs used (from activity log or legacy tools list)
        activity = msg.get("activity_entries") or []
        if activity:
            with st.expander("🔧 Tools, agents & APIs used", expanded=False):
                for e in activity:
                    tool = e.get("tool", "?")
                    api = e.get("api", "—")
                    sub = e.get("sub_agent")
                    preview = e.get("args_preview", "")
                    if sub:
                        st.markdown(f"- **{tool}** → **{sub}** — *{api}*")
                    else:
                        st.markdown(f"- **{tool}** — *{api}*")
                    if preview:
                        st.caption(f"  `{preview}`")
        elif msg.get("tools"):
            st.caption("Tools used (orchestrator + sub-agents):")
            tools = msg["tools"]
            task_calls = [t for t in tools if "task" in t.lower()]
            other_tools = [t for t in tools if t not in task_calls]
            if task_calls:
                st.markdown("- **Sub-agent delegations:** " + ", ".join(task_calls))
            if other_tools:
                st.markdown("\n".join(f"- {t}" for t in other_tools))

if prompt := st.chat_input("Ask a financial question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.container():
            st.caption("**Live: tools, agents & APIs**")
            activity_container = st.empty()
        message_placeholder = st.empty()
        with st.spinner("Researching..."):
            chart_jsons = []
            activity_entries = []
            try:
                agent = get_agent()
                full_response, tool_calls_used, chart_jsons, activity_entries = stream_agent_into_ui(
                    agent, prompt, st.session_state.thread_id, message_placeholder, activity_placeholder=activity_container
                )
                for cj in chart_jsons:
                    try:
                        import plotly.io as pio
                        fig = pio.from_json(cj)
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception:
                        pass
            except Exception as e:
                err = str(e)
                if len(err) > 500:
                    err = err[:500] + "..."
                full_response = (
                    "**Something went wrong.**\n\n```\n{err}\n```\n\n"
                    "**Checks:** Ensure `FIREWORKS_API_KEY` is set in `.env`; Unbrowse is running (`unbrowse setup`). Yahoo and Unbrowse are the primary data sources; set `EXA_API_KEY` for optional web search."
                ).format(err=err)
                tool_calls_used = []
                chart_jsons = []
                activity_entries = []
                message_placeholder.markdown(full_response)

    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response,
        "tools": tool_calls_used,
        "charts": chart_jsons,
        "activity_entries": activity_entries,
    })
