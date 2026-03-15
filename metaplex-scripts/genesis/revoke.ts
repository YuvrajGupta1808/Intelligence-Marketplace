#!/usr/bin/env npx tsx
/**
 * Revoke mint and freeze authorities when the launch is complete (irreversible).
 * Requires GENESIS_ACCOUNT and GENESIS_BASE_MINT from launch output.
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
  if (!process.env.GENESIS_ACCOUNT || !process.env.GENESIS_BASE_MINT) {
    console.error("Set GENESIS_ACCOUNT and GENESIS_BASE_MINT in .env");
    process.exit(1);
  }
  console.log("Revoke: use Metaplex Genesis dashboard or SDK revokeV2 to revoke mint/freeze authorities.");
  console.log("This is irreversible. See: https://developers.metaplex.com/tokens/launch-token");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
