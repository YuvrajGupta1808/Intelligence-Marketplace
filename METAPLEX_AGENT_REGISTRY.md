# Metaplex Agent Registry — Verification for Judges

This document shows how this project satisfies the **Metaplex Agentic Funding & Coordination** track: the agent is registered on Solana with an on-chain identity (Metaplex Core asset) and a live, payment-gated deployment.

**Metaplex Developer Hub:** [https://www.metaplex.com/docs](https://www.metaplex.com/docs)

### For judges — quick checklist

| Requirement | How to verify |
|-------------|----------------|
| **Register an agent** | Agent registered via 8004 (Metaplex Core). See [Registered Agent](#registered-agent-on-chain) and [Explorer link](#verify-on-solana-explorer-devnet). |
| **Read agent data** | **From app:** Open [live app](https://intelligence-marketplace.streamlit.app/), expand **Metaplex Agent Registry — Verify identity**. **From CLI:** `cd metaplex-scripts && AGENT_ASSET=GNdop5oApBkRfH5YDZPDkVKBudENNwaXLmykEg6U5Gmm npm run verify`. |
| **Launch a token (Genesis)** | Scripts in `metaplex-scripts/genesis/`: `npm run launch` (then crank, claim, revoke). Token utility stated [below](#genesis-token-phase-2). |
| **Agent-to-agent commerce (x402)** | `POST /run` returns 402 when unpaid; with `Payment-Signature` header runs the agent. See [x402 API](#x402-api-phase-3--agent-to-agent-commerce). Use the [Next.js web app](apps/web/README.md) for a professional UI that talks to the API. |

---

## Testing Metaplex — flow and endpoints

End-to-end flow and how to test each part.

### Overall flow

```
Register agent (one-time) → Read/verify agent (UI or CLI) → [Optional] Launch token (Genesis) → Use agent (Streamlit or x402 API)
                                                                                                    ↓
                                                                                    Unpaid → 402 + quote → Pay on Solana → Retry with Payment-Signature → 200 + result
```

---

### 1. Read / verify agent (Phase 1)

**What it proves:** The agent has an on-chain identity (Metaplex Core asset) and an operational wallet; judges can confirm both.

**UI (Streamlit):**

1. Open the app: [intelligence-marketplace.streamlit.app](https://intelligence-marketplace.streamlit.app/) or run locally: `cd langgraph_agent && streamlit run streamlit_app.py`.
2. Expand **Metaplex Agent Registry — Verify identity**.
3. Check: **Agent asset**, **Operational wallet**, **Network** (devnet).
4. Click **View on Solana Explorer** → opens devnet Explorer for the agent asset. Confirm the asset and wallet exist on-chain.

**CLI:**

```bash
cd metaplex-scripts
export AGENT_ASSET=GNdop5oApBkRfH5YDZPDkVKBudENNwaXLmykEg6U5Gmm
npm run verify
```

Expected: script reads agent data (e.g. via 8004 / Metaplex Core) and prints that the agent was found, with owner and operational wallet.

**Endpoints:** No HTTP API for “read agent” in this repo — verification is via the Streamlit UI and the `metaplex-scripts` verify script (which talks to Solana/Metaplex under the hood).

---

### 2. Launch a token — Genesis (Phase 2)

**What it proves:** You can create and manage an SPL token launch (Launch Pool) via Metaplex Genesis.

**Flow:** Launch → (after deposit window) Crank → Users Claim → (when done) Revoke authorities.

**Test steps:**

1. **Env:** In `metaplex-scripts/genesis/` (or parent), set `SOLANA_PRIVATE_KEY` (base58), and optionally `SOLANA_RPC_URL` (default devnet), `TOKEN_NAME`, `TOKEN_SYMBOL`, `FUNDS_RECIPIENT` (agent operational wallet). Genesis API requires **raise goal ≥ 250 SOL** (set `LAUNCH_RAISE_GOAL_SOL=250` in `genesis/.env`).

2. **Fund the launch wallet:** The wallet derived from `SOLANA_PRIVATE_KEY` needs ~0.02 SOL on devnet for transaction fees. Run `npm run launch` once to print the launch wallet, then:
   ```bash
   solana airdrop 2 <LAUNCH_WALLET> --url devnet
   ```

3. **Launch (create token + Launch Pool):**
   ```bash
   cd metaplex-scripts/genesis
   npm run launch
   ```
   Expected: logs mint address and launch link. Save `GENESIS_ACCOUNT` and `GENESIS_BASE_MINT` from output for later.

3. **Crank (after deposit period ends):**
   ```bash
   npm run crank
   ```
   Script points you to Metaplex dashboard/SDK to trigger post-deposit behaviors if needed.

4. **Claim / Revoke:** Run `npm run claim` for user claims; `npm run revoke` when the launch is complete (irreversible).

**Endpoints:** No HTTP API here — everything is via the Genesis scripts and (optionally) the Metaplex dashboard.

---

### 3. Agent-to-agent commerce — x402 API (Phase 3)

**What it proves:** Other agents or clients can “pay then run”: unpaid request gets 402 + quote; after paying on Solana, a request with payment proof runs the agent and returns the result.

**Endpoints:**

| Method | Path    | Purpose                |
|--------|---------|------------------------|
| GET    | `/health` | Liveness; returns `{"status":"ok"}`. |
| POST   | `/run`  | Run the agent. Without payment → 402. With `Payment-Signature` → verify and run, return result. |

**Start the API:**

```bash
cd langgraph_agent && pip install -e . && uvicorn x402_api:app --host 0.0.0.0 --port 8000
```

Set `OPENAI_API_KEY`, `SOLANA_PAY_TO` (or `X402_PAY_TO`), and optionally `SOLANA_RPC_URL`.

**Test flow:**

1. **Health check**
   ```bash
   curl -s http://localhost:8000/health
   ```
   Expected: `{"status":"ok"}` and HTTP 200.

2. **Unpaid request (get quote and 402)**
   ```bash
   curl -s -X POST http://localhost:8000/run \
     -H "Content-Type: application/json" \
     -d '{"query":"What are the main causes of climate change?"}'
   ```
   Expected: HTTP **402**, JSON with `quote_lamports`, `quote_sol`, `receiver`, `network`, `how_to_pay`, and headers such as `Payment-Required`, `X-Quote-Lamports`, `X-Receiver`. The `receiver` is the agent’s operational wallet (same as in the Streamlit “Verify identity” section).

3. **Pay on Solana (devnet)**  
   Send the quoted SOL amount to the `receiver` address from the 402 response (e.g. with Solana CLI or any devnet wallet). Note the **transaction signature** after confirmation.

4. **Paid request (run agent)**
   ```bash
   curl -s -X POST http://localhost:8000/run \
     -H "Content-Type: application/json" \
     -d '{"query":"What are the main causes of climate change?"}' \
     -H "Payment-Signature: YOUR_TX_SIGNATURE" \
     -H "X-Quote-Lamports: QUOTE_LAMPORTS_FROM_402"
   ```
   Replace `YOUR_TX_SIGNATURE` and `QUOTE_LAMPORTS_FROM_402` with the real values.  
   Expected: HTTP **200**, JSON with `final_answer`, `plan`, and `tool_call_log` (on-chain tool payment links).

**Streamlit (same payment flow, different UI):** In the app, enter a goal and click **Run** → you get a plan and quote → send SOL to the shown address on devnet → the run continues automatically when payment is detected (no need to call the API again; the app polls for payment).

---

### Summary

| What to test        | Where              | How |
|---------------------|--------------------|-----|
| Read agent data     | Streamlit + CLI    | Expand “Verify identity” in app; run `npm run verify` in `metaplex-scripts`. |
| Explorer / on-chain | Browser            | Use “View on Solana Explorer” from the app. |
| Genesis token       | `metaplex-scripts/genesis/` | `npm run launch` (then crank, claim, revoke as needed). |
| x402 API            | FastAPI            | `GET /health`, then `POST /run` without payment (402), pay on Solana, then `POST /run` with `Payment-Signature` + `X-Quote-Lamports` (200 + result). |
| Payment flow (UI)   | Streamlit          | Run → plan + quote → pay to shown address → execution continues when payment is detected. |

---

## Metaplex Developer Hub

- **Docs:** [https://www.metaplex.com/docs](https://www.metaplex.com/docs)
- **Agents:** [Register an Agent](https://developers.metaplex.com/agents/register-agent) · [Read Agent Data](https://developers.metaplex.com/agents) · [Run an Agent](https://developers.metaplex.com/agents/run-an-agent)

## Registered Agent (On-Chain)

| Field | Value |
|-------|--------|
| **Agent asset (MPL Core)** | `GNdop5oApBkRfH5YDZPDkVKBudENNwaXLmykEg6U5Gmm` |
| **Network** | Solana devnet |
| **Operational wallet** | `6rmVGBrJrvQaJnBFKBaFSKGZv4DnTHEoe1H1TVa6zaYU` |
| **Service URL** | https://intelligence-marketplace.streamlit.app/ |

### Verify on Solana Explorer (devnet)

- **Agent asset (Core NFT):**  
  [https://explorer.solana.com/address/GNdop5oApBkRfH5YDZPDkVKBudENNwaXLmykEg6U5Gmm?cluster=devnet](https://explorer.solana.com/address/GNdop5oApBkRfH5YDZPDkVKBudENNwaXLmykEg6U5Gmm?cluster=devnet)

### Verify from the live app

Open [intelligence-marketplace.streamlit.app](https://intelligence-marketplace.streamlit.app/), expand **Metaplex Agent Registry — Verify identity**, and use the Explorer link and displayed agent/wallet info.

### Verify via CLI (optional)

From the repo root:

```bash
cd metaplex-scripts
export AGENT_ASSET=GNdop5oApBkRfH5YDZPDkVKBudENNwaXLmykEg6U5Gmm
npm run verify
```

Expected output: agent found, owner and operational wallet printed.

## Live app

- **URL:** https://intelligence-marketplace.streamlit.app/
- **Flow:** Enter a goal → agent returns a plan and quote (SOL) → pay to the shown address on devnet → run continues when payment is detected → per-step tool payouts on-chain.

## Genesis token (Phase 2)

The agent has an optional **SPL token** launched via [Metaplex Genesis](https://developers.metaplex.com/tokens/launch-token) (Launch Pool).

**Token utility (for judges):** *Research Agent Access (RAA): holders get a discount on agent quote prices and can participate in governance over agent configuration.*

**Live launch (for judges):** The RAA token is live on Metaplex Genesis. After running `npm run launch`, the script prints a **launch link** (e.g. `https://www.metaplex.com/token/...`). Open that link to see the official sale page: Launch Pool, 500M / 1B tokens, 2-day sale, 250 SOL graduation minimum, 50% liquidity pool. The same info and a “View on Metaplex” link appear in the [Next.js web app](apps/web/) when you set `NEXT_PUBLIC_GENESIS_LAUNCH_URL` to the launch link. RAA is for utility and governance of the research agent only; it is not an investment product.

### Scripts (devnet)

From `metaplex-scripts/genesis/`:

| Script | Purpose |
|--------|--------|
| `npm run launch` | Create token + Launch Pool (deposit window 48h). Writes mint and launch link. Set `GENESIS_ACCOUNT`, `GENESIS_BASE_MINT` from output for later scripts. |
| `npm run crank` | After deposit period ends: trigger behaviors (e.g. move SOL to unlocked bucket). Use Metaplex dashboard or SDK if needed. |
| `npm run claim` | Users claim tokens (claimLaunchPool). Use Metaplex dashboard or SDK. |
| `npm run revoke` | When launch is complete: revoke mint/freeze authorities (irreversible). |

**Env:** `SOLANA_PRIVATE_KEY` (base58), `SOLANA_RPC_URL` (default devnet). Optional: `TOKEN_NAME`, `TOKEN_SYMBOL`, `TOKEN_IMAGE_URI`, `LAUNCH_RAISE_GOAL_SOL`, `FUNDS_RECIPIENT`.

**Docs:** [Metaplex — Launch a Token](https://developers.metaplex.com/tokens/launch-token).

---

## x402 API (Phase 3 — agent-to-agent commerce)

Other agents or clients can pay via HTTP 402 and run this agent.

**Base URL:** Run the API next to the Streamlit app (or as a separate service), e.g. `http://localhost:8000` or your deployed host.

**Endpoint:** `POST /run`  
**Body:** `{ "query": "Your goal or question" }`

### 402 flow

1. **First request (no payment):**  
   Send `POST /run` with `query` only. The API returns **402 Payment Required** with:
   - JSON body: `quote_lamports`, `quote_sol`, `receiver`, `network`, `how_to_pay`
   - Headers: `Payment-Required`, `X-Quote-Lamports`, `X-Receiver`

2. **Pay on Solana:**  
   Send the quoted SOL amount to `receiver` on the given network (devnet/mainnet). Use any wallet; get the transaction signature after confirmation.

3. **Second request (with payment proof):**  
   Send `POST /run` again with the same `query`, plus:
   - **Header:** `Payment-Signature: <tx_signature>`
   - **Header (recommended):** `X-Quote-Lamports: <value from 402 body>` so the server can verify without re-running the planner.

4. **Response:**  
   On success: 200 with `final_answer`, `plan`, and `tool_call_log` (on-chain tool payment links).

**Example (curl):**
```bash
# 1) Get quote (402)
curl -s -X POST http://localhost:8000/run -H "Content-Type: application/json" -d '{"query":"What are the main causes of climate change?"}'
# 2) After paying, retry with signature
curl -s -X POST http://localhost:8000/run -H "Content-Type: application/json" -d '{"query":"What are the main causes of climate change?"}' \
  -H "Payment-Signature: <your_tx_signature>" -H "X-Quote-Lamports: <from_402_response>"
```

**Deploy:** From repo root, run the API on the same host as Streamlit or separately:
```bash
cd langgraph_agent && pip install -e . && uvicorn x402_api:app --host 0.0.0.0 --port 8000
```
Set `OPENAI_API_KEY`, `SOLANA_PAY_TO` (or `X402_PAY_TO`), and optionally `SOLANA_RPC_URL`.

---

## Implementation

- **Registration:** [metaplex-scripts/register-agent.ts](metaplex-scripts/register-agent.ts) — creates collection + agent metadata (IPFS), registers agent on 8004 Agent Registry (Metaplex Core), sets operational wallet.
- **Runtime:** [langgraph_agent/](langgraph_agent/) — LangGraph plan-and-execute agent; payment receiver and signer are the same wallet as the agent’s operational wallet.
- **Genesis:** [metaplex-scripts/genesis/](metaplex-scripts/genesis/) — Token launch scripts (launch, crank, claim, revoke).
- **x402 API:** [langgraph_agent/x402_api.py](langgraph_agent/x402_api.py) — FastAPI with 402 and payment verification for agent-to-agent commerce.
- **Web (Next.js):** [apps/web/](apps/web/) — React frontend that calls the x402 API (run agent, 402 flow, agent identity). Run with `cd apps/web && npm run dev`.
- **References:** [Metaplex Agents](https://developers.metaplex.com/agents), [Metaplex Tokens](https://developers.metaplex.com/tokens/launch-token), [8004 on Solana](https://quantulabs.github.io/8004-solana/) (agent identity on Metaplex Core).
