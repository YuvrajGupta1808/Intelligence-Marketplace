#!/usr/bin/env npx tsx
/**
 * Register the LangGraph agent on the 8004 Agent Registry (Solana).
 * Uses Metaplex Core NFTs for agent identity.
 *
 * Prerequisites:
 * - SOLANA_PRIVATE_KEY (base58) in .env or env
 * - SOLANA_RPC_URL (default: devnet)
 * - AGENT_SERVICE_URL (e.g. https://your-app.com or http://localhost:8501 for Streamlit)
 * - PINATA_JWT (optional) for IPFS - if not set, uses local IPFS at localhost:5001
 *
 * Docs: https://developers.metaplex.com/agents/register-agent
 * 8004 SDK: https://github.com/QuantuLabs/8004-solana-ts
 */

import "dotenv/config";
import { readFileSync, existsSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";
import { Keypair } from "@solana/web3.js";
import bs58 from "bs58";
import {
  SolanaSDK,
  IPFSClient,
  buildRegistrationFileJson,
  ServiceType,
} from "8004-solana";

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

function getKeypair(): Keypair {
  const key =
    process.env.SOLANA_PRIVATE_KEY ||
    process.env.X402_SOLANA_PRIVATE_KEY;
  if (!key) {
    throw new Error(
      "Set SOLANA_PRIVATE_KEY (base58) in .env or environment"
    );
  }
  try {
    const bytes = bs58.decode(key);
    return Keypair.fromSecretKey(bytes);
  } catch {
    throw new Error(
      "SOLANA_PRIVATE_KEY must be base58-encoded (64-byte secret key)"
    );
  }
}

async function main() {
  loadEnv();

  const rpcUrl =
    process.env.SOLANA_RPC_URL || "https://api.devnet.solana.com";
  const cluster = rpcUrl.includes("devnet") ? "devnet" : "mainnet-beta";
  const serviceUrl =
    process.env.AGENT_SERVICE_URL || "http://localhost:8501";
  const pinataJwt = process.env.PINATA_JWT;

  const signer = getKeypair();
  console.log("Signer (operational wallet):", signer.publicKey.toBase58());
  console.log("Cluster:", cluster);
  console.log("RPC:", rpcUrl);
  console.log("Agent service URL:", serviceUrl);

  if (!pinataJwt) {
    console.warn(
      "\nWarning: PINATA_JWT not set. Using local IPFS (localhost:5001).",
      "\nIf you don't have IPFS running, get a free Pinata JWT at https://pinata.cloud"
    );
  }
  const ipfs = pinataJwt
    ? new IPFSClient({ pinataEnabled: true, pinataJwt })
    : new IPFSClient({ url: "http://localhost:5001" });

  const sdk = new SolanaSDK({
    cluster,
    rpcUrl,
    signer,
    ipfsClient: ipfs,
  });

  console.log("\n1. Creating collection metadata (IPFS)...");
  const collection = await sdk.createCollection({
    name: "Intelligence Marketplace Agents",
    symbol: "IMAG",
    description: "Plan-and-execute research agents with Solana payments",
    image: "https://arweave.net/placeholder",
  });
  console.log("   Collection CID:", collection.cid);
  console.log("   Collection URI:", collection.uri);
  console.log("   Collection pointer:", collection.pointer);

  console.log("\n2. Building agent metadata...");
  const agentMeta = buildRegistrationFileJson({
    name: "Research Agent",
    description:
      "Plan-and-execute agent that answers research questions using web search. Payment-gated on Solana devnet. Pay SOL to run; each step triggers on-chain tool payouts.",
    services: [
      { type: ServiceType.OASF, value: serviceUrl },
    ],
    skills: ["natural_language_processing/natural_language_generation/text_completion"],
    domains: ["technology/software_engineering/software_engineering"],
    active: true,
  });

  console.log("\n3. Uploading agent metadata to IPFS...");
  const agentCid = await ipfs.addJson(agentMeta);
  const metadataUri = `ipfs://${agentCid}`;
  console.log("   Agent metadata URI:", metadataUri);

  console.log("\n4. Registering agent on-chain...");
  const result = await sdk.registerAgent(metadataUri, {
    collectionPointer: collection.pointer!,
    atomEnabled: false,
  });

  const asset = result.asset;
  if (!asset) {
    throw new Error("Registration failed: no asset returned");
  }
  console.log("   Agent asset:", asset.toBase58());

  console.log("\n5. Setting operational wallet (same as signer)...");
  await sdk.setAgentWallet(asset, signer);
  console.log("   Operational wallet:", signer.publicKey.toBase58());

  console.log("\n--- Registration complete ---");
  console.log("Agent asset:", asset.toBase58());
  console.log("Collection pointer:", collection.pointer);
  console.log("Operational wallet:", signer.publicKey.toBase58());
  console.log("\nSave AGENT_ASSET=" + asset.toBase58() + " for run-agent and verify scripts.");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
