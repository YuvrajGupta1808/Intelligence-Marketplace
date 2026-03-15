# Intelligence Marketplace — Web

Next.js UI with the same agent flow as Streamlit: **Metaplex details at the top** (agent identity + RAA token), then **run the agent** (query → quote → pay → paste signature → plan and answer). Proxies to the x402 API so no CORS.

## Setup

```bash
cd apps/web
npm install
```

## Run

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## How it works

- **Top:** Metaplex Agent Registry (agent asset, operational wallet, Explorer links) and RAA token (sale terms, View on Metaplex).
- **Run agent:** Enter goal → Get quote & run → pay shown SOL on devnet → paste tx signature + quote lamports → Submit payment & run → see plan, final answer, and on-chain tool payments. Requests go to `/api/run` (Next.js proxy to x402 API).

## Prerequisites

- **x402 API** running: `cd langgraph_agent && uvicorn x402_api:app --host 0.0.0.0 --port 8000`. Set `X402_API_URL` in `.env` if not at `http://127.0.0.1:8000`.

## Env

| Variable | Description |
|----------|-------------|
| `X402_API_URL` | x402 API base URL for server-side proxy (default: `http://127.0.0.1:8000`) |
| `NEXT_PUBLIC_STREAMLIT_APP_URL` | Streamlit app link in header (default: `http://localhost:8501`) |
| `NEXT_PUBLIC_AGENT_ASSET` | Agent asset ID for display |
| `NEXT_PUBLIC_OPERATIONAL_WALLET` | Operational wallet for display |
| `NEXT_PUBLIC_NETWORK` | `devnet` or `mainnet` for Explorer links |
| `NEXT_PUBLIC_GENESIS_LAUNCH_URL` | RAA token launch page URL (from `npm run launch` in `metaplex-scripts/genesis`) |
