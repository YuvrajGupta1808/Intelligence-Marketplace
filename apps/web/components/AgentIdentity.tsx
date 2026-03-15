"use client";

import { explorerUrl } from "@/lib/api";

const AGENT_ASSET =
  process.env.NEXT_PUBLIC_AGENT_ASSET ||
  "GNdop5oApBkRfH5YDZPDkVKBudENNwaXLmykEg6U5Gmm";
const OPERATIONAL_WALLET =
  process.env.NEXT_PUBLIC_OPERATIONAL_WALLET ||
  "6rmVGBrJrvQaJnBFKBaFSKGZv4DnTHEoe1H1TVa6zaYU";
const NETWORK = process.env.NEXT_PUBLIC_NETWORK || "devnet";

export default function AgentIdentity() {
  const explorerAssetUrl = explorerUrl(AGENT_ASSET, NETWORK);
  const explorerWalletUrl = explorerUrl(OPERATIONAL_WALLET, NETWORK);

  return (
    <section className="rounded-xl border border-border bg-surface-elevated p-6">
      <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-white">
        <span className="text-accent">◆</span> Metaplex Agent Registry
      </h2>
      <p className="mb-4 text-sm text-gray-400">
        This agent is registered on the 8004 Agent Registry (Metaplex Core on
        Solana). Verify on-chain identity and operational wallet below.
      </p>
      <dl className="space-y-3 text-sm">
        <div>
          <dt className="text-gray-500">Agent asset (MPL Core)</dt>
          <dd className="mt-0.5 font-mono text-gray-300 break-all">
            {AGENT_ASSET}
          </dd>
          <a
            href={explorerAssetUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-1 inline-block text-accent hover:text-accent-muted"
          >
            View on Solana Explorer →
          </a>
        </div>
        <div>
          <dt className="text-gray-500">Operational wallet</dt>
          <dd className="mt-0.5 font-mono text-gray-300 break-all">
            {OPERATIONAL_WALLET}
          </dd>
          <a
            href={explorerWalletUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-1 inline-block text-accent hover:text-accent-muted"
          >
            View on Solana Explorer →
          </a>
        </div>
        <div>
          <dt className="text-gray-500">Network</dt>
          <dd className="mt-0.5 text-gray-300">{NETWORK}</dd>
        </div>
      </dl>
      <p className="mt-4 text-xs text-gray-500">
        CLI:{" "}
        <code className="rounded bg-surface px-1.5 py-0.5 font-mono">
          cd metaplex-scripts && AGENT_ASSET={AGENT_ASSET} npm run verify
        </code>
      </p>
    </section>
  );
}
