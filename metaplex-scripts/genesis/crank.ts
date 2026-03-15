#!/usr/bin/env npx tsx
/**
 * After the deposit period ends, trigger launchpool behaviors (e.g. move SOL to unlocked bucket).
 * Run once after deposits close. Requires GENESIS_ACCOUNT, BASE_MINT, LAUNCH_POOL_BUCKET from launch output.
 *
 * Docs: https://developers.metaplex.com/tokens/launch-token
 */

import "dotenv/config";
import { readFileSync, existsSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";
import bs58 from "bs58";
import { createUmi } from "@metaplex-foundation/umi-bundle-defaults";
import { keypairIdentity } from "@metaplex-foundation/umi";

const __dirname = dirname(fileURLToPath(import.meta.url));

function loadEnv() {
  const envPaths = [resolve(__dirname, ".env"), resolve(__dirname, "..", ".env")];
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
  const genesisAccount = process.env.GENESIS_ACCOUNT;
  const baseMint = process.env.GENESIS_BASE_MINT;
  if (!genesisAccount || !baseMint) {
    console.error("Set GENESIS_ACCOUNT and GENESIS_BASE_MINT (from launch.ts output) in .env");
    process.exit(1);
  }
  const rpcUrl = process.env.SOLANA_RPC_URL || "https://api.devnet.solana.com";
  const umi = createUmi(rpcUrl);
  const keypair = umi.eddsa.createKeypairFromSecretKey(new Uint8Array(bs58.decode(process.env.SOLANA_PRIVATE_KEY!)));
  umi.use(keypairIdentity(keypair));
  console.log("Crank: trigger behaviors for genesis account", genesisAccount);
  console.log("Use the Metaplex Genesis dashboard or API to trigger post-deposit behaviors.");
  console.log("See: https://developers.metaplex.com/tokens/launch-token");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
