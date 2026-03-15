# LangGraph Plan-and-Execute Agent

A **plan-and-execute** agent built with LangGraph: it plans steps for your query (number of steps depends on the goal), then runs each step using a **web search** tool (DuckDuckGo). **Solana payment gating** (devnet): the agent quotes a price based on the number of steps; after you pay to the receiver address, the run continues automatically when payment is detected. Each step triggers a real **on-chain tool payout** (SOL transfer) to a configurable tool-provider address.

## Structure

```
langgraph_agent/
├── pyproject.toml              # Dependencies and package config
├── streamlit_app.py            # Streamlit UI (run with streamlit run streamlit_app.py)
├── README.md                   # This file
└── src/
    └── langgraph_agent/        # Package
        ├── __init__.py         # Public API: create_plan_execute_graph
        ├── run.py              # Thin entrypoint for python -m langgraph_agent.run
        ├── core/               # Config, state, pricing
        │   ├── __init__.py
        │   ├── config.py       # get_model(), get_temperature(), Solana env, TOOL_PAYOUT_ADDRESS, payment poll
        │   ├── pricing.py      # compute_quote_lamports(), LAMPORTS_PER_STEP, LAMPORTS_TRANSFER_FEE
        │   └── state.py        # PlanExecuteState (incl. payment fields, tool_call_log)
        ├── solana/             # Payment verification and tool payouts
        │   ├── __init__.py
        │   ├── client.py       # get_solana_kit(), get_solana_tools()
        │   └── payments.py     # receiver_balance_lamports(), check_payment_received(), send_lamports_to_tool_provider()
        ├── prompts/
        │   ├── __init__.py
        │   └── prompts.py      # PLANNER_SYSTEM, EXECUTOR_SYSTEM, SYNTHESIZE_SYSTEM
        ├── tools/
        │   ├── __init__.py
        │   └── search.py       # web_search, get_search_tool (DuckDuckGo)
        ├── graph/              # Graph assembly and nodes
        │   ├── __init__.py     # Exports create_plan_execute_graph
        │   ├── builder.py      # StateGraph build and compile
        │   └── nodes/
        │       ├── __init__.py
        │       ├── planner.py  # planner_node
        │       ├── quote.py    # quote_node (quote from len(plan), receiver)
        │       ├── wait_payment.py # wait_payment_node (poll until payment detected)
        │       ├── executor.py # executor_node (budget check + web_search)
        │       ├── pay_tool.py # pay_tool_node (on-chain transfer to TOOL_PAYOUT_ADDRESS + log)
        │       └── synthesize.py # synthesize_node
        └── cli/
            ├── __init__.py
            └── run.py         # CLI logic: argparse, invoke graph, print answer
```

- **core/**: Shared config (`get_model`, `get_temperature`) and state schema (`PlanExecuteState`).
- **prompts/**: System prompts for planner, executor, and synthesizer.
- **tools/**: Web search tool for the executor.
- **graph/**: Graph construction in `builder.py`; node logic in `graph/nodes/`.
- **cli/**: CLI entrypoint; root `run.py` delegates to `cli.run.main` so `python -m langgraph_agent.run` works.
- **streamlit_app.py**: Web UI with streaming progress (at project root).

## Architecture flow

High-level flow:

```
                    ┌─────────────┐
                    │   START     │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  planner    │  LLM: user goal → steps (length varies by goal)
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   quote     │  quote_lamports = f(len(plan)), receiver
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │wait_payment │  Poll until receiver balance ≥ quote
                    └──────┬──────┘
                           │ paid
                           ▼
                    ┌─────────────┐
          ┌─────────│  executor   │  LLM + web_search for current step
          │         └──────┬──────┘
          │                │
          │                ▼
          │         ┌─────────────┐
          │         │  pay_tool   │  On-chain SOL to TOOL_PAYOUT_ADDRESS
          │         └──────┬──────┘
          │                │
          │                ▼
          │         ┌─────────────┐
          │         │ more steps? │
          │         └──────┬──────┘
          │     yes         │        no
          └────────────────┼─────────────┐
                            │             │
                            ▼             ▼
                     ┌─────────────┐  ┌─────────────┐
                     │  synthesize │  │     END     │
                     └──────┬──────┘  └─────────────┘
                            │
                            ▼
                     ┌─────────────┐
                     │     END     │  final_answer + tool payment links
                     └─────────────┘
```

**State** (simplified):

| Field         | Role |
|---------------|------|
| `query`                       | User goal (input). |
| `plan`                        | Step strings from planner (length depends on goal). |
| `step_index`                  | Current step (0-based). |
| `step_results`                | Search results, one per step. |
| `quote_lamports`              | Price from `compute_quote_lamports(len(plan))`. |
| `payment_receiver`            | Address where user sends SOL. |
| `payment_status`              | `"pending"` or `"confirmed"`. |
| `budget_remaining_lamports`   | Set after payment; decremented each pay_tool. |
| `tool_call_log`               | Per-step: `{ tool, amount_lamports, tx }` (tx = signature or "simulated"/"failed"). |
| `final_answer`                | Output from synthesize. |

**Nodes**:

1. **planner** (goal-driven steps): LLM turns `query` into `plan`. Number and content of steps follow the user's goal (e.g. 1 step for a simple question, 2+ for comparisons or multi-part questions).
2. **quote**: Sets `quote_lamports` from `len(plan)` (per-step + transfer fee + platform fee), `payment_receiver`, and receiver balance snapshot.
3. **wait_payment**: Polls receiver balance until ≥ quote (or timeout). Sets `payment_status=confirmed` and budget. Run continues automatically when payment is detected.
4. **executor**: For `plan[step_index]`, call LLM with the `web_search` tool; run the tool, append the result to `step_results`, increment `step_index`; then the graph routes on whether more steps remain.
5. **pay_tool**: Sends `LAMPORTS_PER_STEP` from agent wallet to `TOOL_PAYOUT_ADDRESS` (on-chain); appends to `tool_call_log` with tx signature or "simulated"/"failed".
6. **synthesize**: LLM produces `final_answer` from `query`, `plan`, and `step_results`.

## Real example

**Query:**

```bash
python -m langgraph_agent.run "What are the main causes of climate change and one recent EU policy about it?"
```

**Example flow:**

1. **Planner** turns the goal into steps (number depends on the goal; here, two steps), e.g.:
   - "Search for main causes of climate change"
   - "Search for recent EU climate policy"
2. **Quote** sets the price from the number of steps; **wait_payment** polls until the user has paid.
3. **Executor** (step 1): calls `web_search("main causes of climate change")`, appends to `step_results`; **pay_tool** sends SOL to `TOOL_PAYOUT_ADDRESS`.
4. **Executor** (step 2): calls `web_search("recent EU climate policy 2024")`, appends to `step_results`; **pay_tool** sends again.
5. **Synthesize**: returns a short final answer (causes + one EU policy). UI shows tool payment links.

**Run from repo root (with `.env` containing `OPENAI_API_KEY`):**

```bash
cd langgraph_agent
pip install -e .
python -m langgraph_agent.run "What are the main causes of climate change and one recent EU policy about it?"
```

Or use a virtual environment so the correct Python is used:

```bash
cd langgraph_agent
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -e .
python -m langgraph_agent.run "What are the main causes of climate change and one recent EU policy about it?"
```

Alternatively with `uv`:

```bash
cd langgraph_agent
uv run python -m langgraph_agent.run "What are the main causes of climate change and one recent EU policy about it?"
```

**Optional:** set `OPENAI_MODEL` in `.env` (e.g. `OPENAI_MODEL=gpt-4o-mini`) or pass `--model gpt-4o` to the script.

### Streamlit UI

Run the web UI from the `langgraph_agent` directory (with `OPENAI_API_KEY` set):

```bash
cd langgraph_agent
pip install -e .
streamlit run streamlit_app.py
```

You get a text area for your goal, an optional model override, and a **Run** button. The app streams the plan, quote, step results, and final answer. After payment is detected, it shows a **Tool payments (on-chain)** section with a Solana Explorer link for each tool payout.

## Payment flow (Solana)

When `SOLANA_PAY_TO` (or `X402_PAY_TO`) is set:

1. **Planner** produces steps (length varies by user goal). **Quote** node sets `quote_lamports = len(plan) * (LAMPORTS_PER_STEP + LAMPORTS_TRANSFER_FEE) + PLATFORM_FEE_LAMPORTS` and the receiver address.
2. **Wait payment**: polls the receiver balance every few seconds until it is ≥ quote (or timeout). The run continues automatically when payment is detected (no "Run again").
3. If not paid in time: run ends and the UI shows "Pay X SOL to &lt;address&gt;".
4. If paid: **executor** runs each step; **pay_tool** sends a real on-chain SOL transfer (`LAMPORTS_PER_STEP`) from the agent wallet to `TOOL_PAYOUT_ADDRESS` and logs the tx; **synthesize** returns the answer. The Streamlit UI shows a **Tool payments (on-chain)** section with links to Solana Explorer for each payout.

**Env:**

- `SOLANA_RPC_URL` – default `https://api.devnet.solana.com`.
- `SOLANA_PRIVATE_KEY` (or `X402_SOLANA_PRIVATE_KEY`) – agent wallet private key (base58). This wallet signs tool payouts; it must have SOL (e.g. set `SOLANA_PAY_TO` to this wallet's public key so user payment funds it).
- `SOLANA_PAY_TO` (or `X402_PAY_TO`) – address where the user sends the quote (base58).
- `TOOL_PAYOUT_ADDRESS` – address that receives each per-step tool payout (base58). If unset, pay_tool logs "simulated" and no transfer is sent.
- Optional: `PAYMENT_POLL_INTERVAL_SEC`, `PAYMENT_POLL_MAX_WAIT_SEC` – polling while waiting for payment.
- Optional pricing (lamports): `TOOL_PRICE_LAMPORTS_WEB_SEARCH`, `LAMPORTS_TRANSFER_FEE`, `PLATFORM_FEE_LAMPORTS`.

**Paying user:** Send the quoted SOL to `SOLANA_PAY_TO` on devnet. The run continues automatically when the balance is detected (no "Run again"). Tool payouts are sent to `TOOL_PAYOUT_ADDRESS` after each step; confirm in the UI's "Tool payments" section or on Solana Explorer.

If `SOLANA_PAY_TO` is not set, the graph runs without payment (no gate).

## Metaplex Agent Registry (optional)

To register this agent on the **8004 Agent Registry** (Metaplex Core NFTs on Solana) for on-chain identity and discoverability:

```bash
# Option A: From metaplex-scripts
cd ../metaplex-scripts
cp .env.example .env
# Add PINATA_JWT (from pinata.cloud) and ensure SOLANA_PRIVATE_KEY is set
npm install && npm run register

# Option B: Python wrapper (requires pip install -e . in langgraph_agent)
python -m langgraph_agent.metaplex register
```

See [metaplex-scripts/README.md](../metaplex-scripts/README.md) for details. Docs: [Metaplex Agents](https://developers.metaplex.com/agents), [8004 on Solana](https://quantulabs.github.io/8004-solana/).

## Requirements

- Python 3.10+
- `OPENAI_API_KEY` in the environment or in a `.env` file (project or repo root)
- No API key needed for web search (DuckDuckGo)
- For payment: `solana` (PyPI) for balance checks; optional `solana-agent-kit-py` for Solana tools: `pip install langgraph-agent[solana-kit]`

## Optional: use as a library

```python
from langgraph_agent import create_plan_execute_graph

graph = create_plan_execute_graph(model="gpt-4o-mini")
result = graph.invoke({"query": "What is the capital of France and its population?"})
print(result["final_answer"])
```
