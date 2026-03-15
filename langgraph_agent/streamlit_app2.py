"""Streamlit UI for the plan-and-execute agent (with quote and payment)."""

import os
from pathlib import Path

import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
    root = Path(__file__).resolve().parents[1]
    for d in (Path(__file__).resolve().parent, root):
        if (d / ".env").exists():
            load_dotenv(d / ".env")
    # Also load apps/web/.env so NEXT_PUBLIC_* (agent asset, wallet, network, genesis URL) are visible in UI
    web_env = root / "apps" / "web" / ".env"
    if web_env.exists():
        load_dotenv(web_env)
except ImportError:
    pass

from langgraph_agent import create_plan_execute_graph
from langgraph_agent.core.pricing import lamports_to_sol


st.set_page_config(page_title="Intelligence-Marketplace", page_icon="🔍", layout="wide")
st.title("Intelligence-Marketplace")
st.caption("Enter a goal; agent returns a plan and quote. Send the payment — the run continues automatically when payment is detected.")

# Placeholder: stocks scraped from web (replace with real scrape when available)
STOCKS_FROM_WEB = [
    "AAPL", "GOOGL", "MSFT", "AMZN", "META", "NVDA", "TSLA", "JPM", "V", "WMT",
]

left_col, right_col = st.columns([1, 2])

with left_col:
    # Left top: list of stocks (from web scrape)
    st.subheader("Stocks (from web)")
    for ticker in STOCKS_FROM_WEB:
        st.markdown(f"- {ticker}")

    # Left bottom: Metaplex agent
    st.subheader("Metaplex Agent")
    agent_asset = os.getenv("NEXT_PUBLIC_AGENT_ASSET") or os.getenv("AGENT_ASSET", "GNdop5oApBkRfH5YDZPDkVKBudENNwaXLmykEg6U5Gmm")
    operational_wallet = (
        os.getenv("NEXT_PUBLIC_OPERATIONAL_WALLET")
        or os.getenv("SOLANA_PAY_TO")
        or os.getenv("X402_PAY_TO")
        or "6rmVGBrJrvQaJnBFKBaFSKGZv4DnTHEoe1H1TVa6zaYU"
    )
    cluster = (
        os.getenv("NEXT_PUBLIC_NETWORK")
        or ("devnet" if "devnet" in (os.getenv("SOLANA_RPC_URL") or "").lower() else "mainnet")
    )
    genesis_launch_url = os.getenv(
        "NEXT_PUBLIC_GENESIS_LAUNCH_URL",
        "https://www.metaplex.com/token/UKBsjo8vkazhyhyrjJUr2SBrCzvybKQd73k9fJaPLEX?network=solana-devnet",
    )
    explorer_url = f"https://explorer.solana.com/address/{agent_asset}?cluster={cluster}"
    st.markdown("Registered on 8004 Agent Registry (Metaplex Core on Solana).")
    st.markdown(f"**Agent asset:** `{agent_asset}`")
    st.markdown(f"**Operational wallet:** `{operational_wallet}`")
    st.markdown(f"**Network:** {cluster}")
    st.markdown(f"**Genesis RAA launch:** [Open launch page]({genesis_launch_url})")
    st.markdown(f"[View on Solana Explorer]({explorer_url})")
    st.markdown("To verify from CLI: `cd metaplex-scripts && AGENT_ASSET=" + agent_asset + " npm run verify`")

with right_col:
    # Right: chat / planner interface
    query = st.text_area(
        "Your goal or question",
        placeholder="e.g. What are the main causes of climate change and one recent EU policy?",
        height=100,
    )
    model_override = st.text_input("Model (optional)", value=os.getenv("OPENAI_MODEL", ""), placeholder="gpt-4o-mini")

    if st.button("Run", type="primary"):
        if not query or not query.strip():
            st.warning("Enter a goal or question.")
            st.stop()
        if not os.getenv("OPENAI_API_KEY"):
            st.error("Set OPENAI_API_KEY in the environment or in a .env file.")
            st.stop()

        graph = create_plan_execute_graph(model=model_override or None)
        plan_ph = st.empty()
        quote_ph = st.empty()
        steps_ph = st.empty()
        answer_ph = st.empty()
        payouts_ph = st.empty()

        step_results_acc: list[str] = []
        tool_call_log: list[dict] = []
        quote_lamports: int | None = None
        payment_receiver: str | None = None
        payment_confirmed = False
        explorer_cluster = "devnet" if "devnet" in (os.getenv("SOLANA_RPC_URL") or "").lower() else "mainnet"

        try:
            for chunk in graph.stream(
                {"query": query.strip()},
                stream_mode="updates",
            ):
                for node_name, state_update in chunk.items():
                    if node_name == "planner":
                        plan = state_update.get("plan") or []
                        plan_ph.markdown("**Plan**\n\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(plan)))
                    elif node_name == "quote":
                        quote_lamports = state_update.get("quote_lamports") or 0
                        payment_receiver = state_update.get("payment_receiver") or ""
                        sol = lamports_to_sol(quote_lamports)
                        quote_ph.markdown(
                            f"**Quote**\n\nPay **{sol:.6f} SOL** to `{payment_receiver}` (devnet). "
                            "The run will continue automatically when payment is detected (no need to click Run again)."
                        )
                    elif node_name == "wait_payment":
                        if state_update.get("payment_status") == "confirmed":
                            payment_confirmed = True
                    elif node_name == "executor":
                        payment_confirmed = True
                        step_results_acc.extend(state_update.get("step_results") or [])
                        with steps_ph.container():
                            st.markdown("**Step results**")
                            for i, res in enumerate(step_results_acc):
                                st.expander(f"Step {i+1}", expanded=(i == len(step_results_acc) - 1)).write(
                                    res[:3000] + ("..." if len(res) > 3000 else "")
                                )
                    elif node_name == "pay_tool":
                        tool_call_log = state_update.get("tool_call_log") or tool_call_log
                    elif node_name == "synthesize":
                        tool_call_log = state_update.get("tool_call_log") or tool_call_log
                        answer_ph.markdown("**Final answer**\n\n" + (state_update.get("final_answer") or ""))

            if tool_call_log:
                with payouts_ph.container():
                    st.markdown("**Tool payments (on-chain)**")
                    for i, entry in enumerate(tool_call_log):
                        tool = entry.get("tool", "—")
                        lamports = entry.get("amount_lamports", 0)
                        tx = entry.get("tx", "")
                        sol_str = f"{lamports_to_sol(lamports):.6f} SOL"
                        if tx and tx not in ("simulated", "failed"):
                            url = f"https://explorer.solana.com/tx/{tx}?cluster={explorer_cluster}"
                            st.markdown(f"- **{tool}**: {sol_str} — [View transaction]({url})")
                        else:
                            st.markdown(f"- **{tool}**: {sol_str} — `{tx}`")
            if not payment_confirmed and quote_lamports is not None and payment_receiver:
                st.info(f"Payment required: send {lamports_to_sol(quote_lamports):.6f} SOL to `{payment_receiver}` (devnet). The app will continue automatically when payment is detected (up to ~5 min).")
        except Exception as e:
            st.error(str(e))
            raise
