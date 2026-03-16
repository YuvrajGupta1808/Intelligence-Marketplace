/**
 * Metaplex "Run an Agent" — executive profile + delegate execution.
 *
 * This is a REFERENCE implementation for when @metaplex-foundation/mpl-agent-registry
 * is installable (it currently has a broken "link:" dependency on npm).
 *
 * Docs: https://developers.metaplex.com/agents/run-an-agent
 *
 * Flow:
 * 1. Register executive profile (one-time per wallet): registerExecutiveV1(umi, { payer })
 * 2. Delegate execution (asset owner links agent to executive): delegateExecutionV1(umi, { agentAsset, agentIdentity, executiveProfile })
 *
 * Prerequisites:
 * - Agent must be registered with registerIdentityV1 (mpl-agent-registry), not only 8004.
 * - Install: npm install @metaplex-foundation/mpl-agent-registry @metaplex-foundation/umi-bundle-defaults
 *
 * Uncomment and adapt once the package install works.
 */
/*
import "dotenv/config";
import { readFileSync, existsSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";
import { createUmi } from "@metaplex-foundation/umi-bundle-defaults";
import { keypairIdentity } from "@metaplex-foundation/umi";
import { mplAgentIdentity, mplAgentTools } from "@metaplex-foundation/mpl-agent-registry";
import {
  registerExecutiveV1,
  delegateExecutionV1,
  findAgentIdentityV1Pda,
  findExecutiveProfileV1Pda,
} from "@metaplex-foundation/mpl-agent-registry";
import { createKeypairFromSecretKey } from "@solana/web3.js";
import bs58 from "bs58";

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
  const rpcUrl = process.env.SOLANA_RPC_URL || "https://api.devnet.solana.com";
  const assetStr = process.env.AGENT_ASSET;
  if (!assetStr) {
    console.error("Set AGENT_ASSET");
    process.exit(1);
  }

  const keypair = createKeypairFromSecretKey(bs58.decode(process.env.SOLANA_PRIVATE_KEY!));
  const umi = createUmi(rpcUrl)
    .use(mplAgentIdentity())
    .use(mplAgentTools())
    .use(keypairIdentity(umi, keypair));

  const agentAsset = publicKey(assetStr);

  // 1. Register executive profile (idempotent per wallet; may fail if already exists)
  console.log("Registering executive profile...");
  await registerExecutiveV1(umi, { payer: umi.payer }).sendAndConfirm(umi);
  console.log("Executive profile registered.");

  // 2. Delegate execution (owner links agent to this executive)
  const agentIdentity = findAgentIdentityV1Pda(umi, { asset: agentAsset });
  const executiveProfile = findExecutiveProfileV1Pda(umi, { authority: umi.payer.publicKey });
  console.log("Delegating execution...");
  await delegateExecutionV1(umi, {
    agentAsset,
    agentIdentity,
    executiveProfile,
  }).sendAndConfirm(umi);
  console.log("Delegation complete. Agent can now be run by this executive.");
}
main().catch((e) => { console.error(e); process.exit(1); });
*/

export {};
