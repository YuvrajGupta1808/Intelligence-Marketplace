"use client";

const GENESIS_LAUNCH_URL =
  process.env.NEXT_PUBLIC_GENESIS_LAUNCH_URL || "";
const TOKEN_NAME = "Research Agent Access";
const TOKEN_SYMBOL = "RAA";

export default function RaaTokenSection() {
  return (
    <section className="rounded-xl border border-border bg-surface-elevated p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-white">
          <span className="text-accent">◆</span> {TOKEN_NAME} ({TOKEN_SYMBOL})
        </h2>
        {GENESIS_LAUNCH_URL ? (
          <a
            href={GENESIS_LAUNCH_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-lg bg-accent/20 px-3 py-1.5 text-sm font-medium text-accent hover:bg-accent/30"
          >
            View on Metaplex →
          </a>
        ) : (
          <span className="text-xs text-gray-500">
            Set NEXT_PUBLIC_GENESIS_LAUNCH_URL for link
          </span>
        )}
      </div>

      <p className="mb-4 text-sm text-gray-400">
        Official community token for the Intelligence Marketplace research agent,
        launched via Metaplex Genesis. Holders get a discount on agent quote
        prices and can participate in governance over agent configuration.
      </p>

      <div className="grid gap-4 rounded-lg border border-border/80 bg-surface/50 p-4 sm:grid-cols-2">
        <div>
          <dt className="text-xs font-medium uppercase tracking-wider text-gray-500">
            Sale type
          </dt>
          <dd className="mt-0.5 text-sm font-medium text-white">
            Launch Pool
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-wider text-gray-500">
            Tokens for sale
          </dt>
          <dd className="mt-0.5 text-sm font-medium text-white">
            500M / 1B
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-wider text-gray-500">
            Sale duration
          </dt>
          <dd className="mt-0.5 text-sm font-medium text-white">
            2 days (48h)
          </dd>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-wider text-gray-500">
            Graduation minimum
          </dt>
          <dd className="mt-0.5 text-sm font-medium text-white">
            250 SOL
          </dd>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap gap-4 text-xs text-gray-500">
        <span>Distribution: Launch Pool 50% · LP 25% · Unlocked 25%</span>
      </div>

      <p className="mt-4 text-xs text-gray-500 italic">
        This token is for utility and governance of the research agent only. It
        is not an investment product. Participate only on Metaplex and official
        project channels.
      </p>
    </section>
  );
}
