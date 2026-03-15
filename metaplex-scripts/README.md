# Metaplex Agent Registry Scripts

Scripts to register the LangGraph plan-and-execute agent on the **8004 Agent Registry** (Solana), which uses Metaplex Core NFTs for agent identity and discoverability.

- [8004 on Solana](https://quantulabs.github.io/8004-solana/)
- [Metaplex Agents](https://developers.metaplex.com/agents)

## Prerequisites

1. **Solana wallet** — Use the same `SOLANA_PRIVATE_KEY` as your LangGraph agent (from repo root `.env`).
2. **IPFS** — Either:
   - **Pinata** (recommended): Get a free JWT at [pinata.cloud](https://pinata.cloud), set `PINATA_JWT` in `.env`.
   - **Local IPFS**: Run `ipfs daemon` and use `localhost:5001` (no env needed).

## Quick Start

```bash
# 1. Copy env and add PINATA_JWT (or run local IPFS)
cp .env.example .env
# Edit .env: add SOLANA_PRIVATE_KEY, PINATA_JWT

# 2. Install and register
npm install
npm run register
```

The script will:

1. Create collection metadata and upload to IPFS
2. Build agent metadata (name, description, services)
3. Upload agent metadata to IPFS
4. Register the agent on-chain (8004 devnet)
5. Set the operational wallet (same as your signer)

Save the printed `AGENT_ASSET` for the verify script.

## Verify Registration

```bash
AGENT_ASSET=<agent_asset_pubkey> npm run verify
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SOLANA_PRIVATE_KEY` | Yes | Base58-encoded private key (64 bytes) |
| `PINATA_JWT` | Yes* | Pinata JWT for IPFS (*or run local IPFS) |
| `SOLANA_RPC_URL` | No | Default: `https://api.devnet.solana.com` |
| `AGENT_SERVICE_URL` | No | Default: `http://localhost:8501` (Streamlit) |
| `AGENT_ASSET` | For verify | Agent asset pubkey from `npm run register` |

## Scripts

- `npm run register` — Register agent (create collection, upload metadata, register, set wallet)
- `npm run verify` — Verify agent is registered (requires `AGENT_ASSET`)
- `npm run run-agent` — Alias for verify (8004 uses operational wallet; no separate delegation step)

## Integration with LangGraph Agent

The agent’s **operational wallet** (set by `setAgentWallet`) is the same wallet used for:

- Receiving user payments (`SOLANA_PAY_TO`)
- Signing tool payouts (`SOLANA_PRIVATE_KEY`)

So the LangGraph runtime is already “running” the agent on-chain. No extra delegation step is needed for 8004.
