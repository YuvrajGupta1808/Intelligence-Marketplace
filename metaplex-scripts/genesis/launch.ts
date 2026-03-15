#!/usr/bin/env npx tsx
/**
 * Metaplex Genesis: create and register a token launch (Launch Pool) for the Research Agent.
 * Run once to create the token and activate the launch.
 *
 * Env: SOLANA_PRIVATE_KEY (base58), SOLANA_RPC_URL (default devnet).
 * Optional: TOKEN_NAME, TOKEN_SYMBOL, TOKEN_IMAGE_URI, LAUNCH_RAISE_GOAL_SOL, FUNDS_RECIPIENT
 *
 * Docs: https://developers.metaplex.com/tokens/launch-token
 */

import "dotenv/config";
import { readFileSync, existsSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";
import bs58 from "bs58";
import { createUmi } from "@metaplex-foundation/umi-bundle-defaults";
import { createAndRegisterLaunch } from "@metaplex-foundation/genesis";
import { keypairIdentity } from "@metaplex-foundation/umi";

const __dirname = dirname(fileURLToPath(import.meta.url));

function loadEnv() {
  const envPaths = [resolve(__dirname, ".env"), resolve(__dirname, "..", ".env"), resolve(__dirname, "..", "..", ".env")];
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
    }
  }
}

function getSecretKeyBytes(): Uint8Array {
  const key = process.env.SOLANA_PRIVATE_KEY || process.env.X402_SOLANA_PRIVATE_KEY;
  if (!key) throw new Error("Set SOLANA_PRIVATE_KEY (base58) in .env or environment.");
  return new Uint8Array(bs58.decode(key));
}

async function main() {
  loadEnv();
  const rpcUrl = process.env.SOLANA_RPC_URL || "https://api.devnet.solana.com";
  const umi = createUmi(rpcUrl);
  const keypair = umi.eddsa.createKeypairFromSecretKey(getSecretKeyBytes());
  umi.use(keypairIdentity(keypair));

  // Launch wallet needs ~0.02 SOL for tx fees on devnet. If using devnet, run: solana airdrop 2 <WALLET>
  const walletPk = umi.identity.publicKey;
  console.log("Launch wallet:", walletPk);

  const tokenName = process.env.TOKEN_NAME || "Research Agent Access";
  const tokenSymbol = process.env.TOKEN_SYMBOL || "RAA";
  // Token image must be Irys URL (https://gateway.irys.xyz/...); set TOKEN_IMAGE_URI or upload to Irys first
  const tokenImage = process.env.TOKEN_IMAGE_URI || "https://gateway.irys.xyz/placeholder";
  const raiseGoalSol = Number(process.env.LAUNCH_RAISE_GOAL_SOL || "10");
  const fundsRecipient = process.env.FUNDS_RECIPIENT || umi.identity.publicKey;

  // Deposit period opens in 1 hour and lasts 48h (Genesis API may require start in future)
  const depositStart = new Date(Date.now() + 60 * 60 * 1000);
  const raiseGoal = raiseGoalSol;

  const network = rpcUrl.includes("devnet") ? "solana-devnet" : "solana-mainnet";
  const input = {
    wallet: umi.identity.publicKey,
    launchType: "project" as const,
    network,
    token: { name: tokenName, symbol: tokenSymbol, image: tokenImage },
    launch: {
      launchpool: {
        tokenAllocation: 500_000_000,
        depositStartTime: depositStart,
        raiseGoal,
        raydiumLiquidityBps: 5000,
        fundsRecipient,
      },
    },
  };

  console.log("Creating and registering launch...");
  console.log("Token:", tokenName, tokenSymbol);
  console.log("Deposit window: 48h from", depositStart.toISOString());
  console.log("Raise goal:", raiseGoalSol, "SOL");
  const result = await createAndRegisterLaunch(umi, {}, input);
  console.log("Mint:", result.mintAddress);
  const launchLink = result.launch?.link ?? "";
  console.log("Launch link:", launchLink);
  if (launchLink) {
    console.log("Set in apps/web/.env: NEXT_PUBLIC_GENESIS_LAUNCH_URL=" + launchLink);
  }
}

main().catch((e: unknown) => {
  console.error(e);
  const err = e as { responseBody?: { details?: unknown } };
  if (err?.responseBody?.details) {
    console.error("Validation details:", JSON.stringify(err.responseBody.details, null, 2));
  }
  process.exit(1);
});
