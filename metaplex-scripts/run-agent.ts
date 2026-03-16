#!/usr/bin/env npx tsx
import "dotenv/config";
/**
 * Verify the agent is registered, then print how to run it.
 * "Run an agent" = agent is registered and operational wallet is set;
 * you then start the backend (chat_api or Streamlit) and use the app.
 *
 * Prerequisites:
 * - AGENT_ASSET (from npm run register)
 * - SOLANA_RPC_URL (optional)
 *
 * Usage: AGENT_ASSET=<pubkey> npm run run-agent
 *
 * For Metaplex "Run an Agent" (executive profile + delegate execution), see
 * delegate-execution-metaplex.example.ts and the docs when
 * @metaplex-foundation/mpl-agent-registry is installable.
 */

import { readFileSync, existsSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";
import { SolanaSDK } from "8004-solana";
import { PublicKey } from "@solana/web3.js";

const __dirname = dirname(fileURLToPath(import.meta.url));

function loadEnv() {
  const envPaths = [
    resolve(__dirname, ".env"),
    resolve(__dirname, "..", ".env"),
  ];
  for (const p of envPaths) {
    if (existsSync(p)) {
      const content = readFileSync(p, "utf-8");
      for (const line of content.split("\n")) {
        const m = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$/);
        if (m && !process.env[m[1]]) {
          const val = m[2].replace(/^["']|["']$/g, "").trim();
          if (val) process.env[m[1]] = val;
        }
      }
      break;
    }
  }
}

async function main() {
  loadEnv();

  const assetStr = process.env.AGENT_ASSET;
  if (!assetStr) {
    console.error("Set AGENT_ASSET to the agent asset public key from register-agent.ts");
    console.error("Example: AGENT_ASSET=GNdop5oApBkRfH5YDZPDkVKBudENNwaXLmykEg6U5Gmm npm run run-agent");
    process.exit(1);
  }

  const rpcUrl =
    process.env.SOLANA_RPC_URL || "https://api.devnet.solana.com";
  const cluster = rpcUrl.includes("devnet") ? "devnet" : "mainnet-beta";
  const serviceUrl = process.env.AGENT_SERVICE_URL || "http://localhost:8501";

  const sdk = new SolanaSDK({ cluster, rpcUrl });
  const asset = new PublicKey(assetStr);

  console.log("Run an Agent — verifying registration...\n");
  console.log("Agent asset:", assetStr);
  console.log("Cluster:", cluster);

  try {
    const agent = await sdk.loadAgent(asset);
    if (!agent) {
      console.error("Agent not found. Register first: npm run register");
      process.exit(1);
    }

    const owner = agent.getOwnerPublicKey().toBase58();
    const wallet = agent.getAgentWalletPublicKey();
    const operationalWallet = wallet?.toBase58() ?? "(not set)";

    console.log("\n--- Agent ready to run ---");
    console.log("Asset:", asset.toBase58());
    console.log("Owner:", owner);
    console.log("Operational wallet:", operationalWallet);

    if (!wallet) {
      console.error("\nOperational wallet not set. Re-run registration or setAgentWallet.");
      process.exit(1);
    }

    console.log("\n--- How to run the agent ---");
    console.log("1. Start the chat API (from repo root):");
    console.log("   cd langgraph_agent && pip install -e . && uvicorn chat_api:app --host 0.0.0.0 --port 7001");
    console.log("");
    console.log("2. Start the front-end (e.g. Deep Research page):");
    console.log("   cd Front-End && npm run dev");
    console.log("   Then open the Deep Research page and submit a query.");
    console.log("");
    console.log("   Or run Streamlit:");
    console.log("   cd langgraph_agent && streamlit run streamlit_app.py");
    console.log("");
    console.log("3. Ensure .env has OPENAI_API_KEY and SOLANA_PAY_TO (or SOLANA_PRIVATE_KEY) set.");
    console.log("   Agent service URL in registration:", serviceUrl);
    console.log("\nDone. Agent is registered; start the backend and use the app to run it.");
  } catch (err) {
    console.error("Error loading agent:", err);
    process.exit(1);
  }
}

main();
