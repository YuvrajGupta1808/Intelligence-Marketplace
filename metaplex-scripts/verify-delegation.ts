#!/usr/bin/env npx tsx
import "dotenv/config";
/**
 * Verify agent registration on the 8004 Agent Registry.
 *
 * Prerequisites:
 * - AGENT_ASSET (agent asset public key from register-agent.ts)
 * - SOLANA_RPC_URL (optional)
 *
 * Usage: AGENT_ASSET=<pubkey> npm run verify
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
    process.exit(1);
  }

  const rpcUrl =
    process.env.SOLANA_RPC_URL || "https://api.devnet.solana.com";
  const cluster = rpcUrl.includes("devnet") ? "devnet" : "mainnet-beta";

  const sdk = new SolanaSDK({ cluster, rpcUrl });
  const asset = new PublicKey(assetStr);

  console.log("Verifying agent:", assetStr);
  console.log("Cluster:", cluster);

  try {
    const agent = await sdk.loadAgent(asset);
    if (!agent) {
      console.error("Agent not found");
      process.exit(1);
    }
    console.log("\n--- Agent found ---");
    console.log("Asset:", asset.toBase58());
    console.log("Owner:", agent.getOwnerPublicKey().toBase58());
    const wallet = agent.getAgentWalletPublicKey();
    console.log("Operational wallet:", wallet?.toBase58() ?? "(not set)");
  } catch (err) {
    console.error("Agent not found or error:", err);
    process.exit(1);
  }
}

main();
