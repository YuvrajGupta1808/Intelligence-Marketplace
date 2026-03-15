import AgentIdentity from "@/components/AgentIdentity";
import RaaTokenSection from "@/components/RaaTokenSection";
import RunAgent from "@/components/RunAgent";

const STREAMLIT_APP_URL =
  process.env.NEXT_PUBLIC_STREAMLIT_APP_URL || "http://localhost:8501";

export default function Home() {
  return (
    <div className="min-h-screen bg-surface">
      <header className="sticky top-0 z-10 border-b border-border bg-surface-elevated/95 backdrop-blur">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-4 sm:px-6">
          <div className="flex items-center gap-3">
            <span className="text-xl font-semibold text-white">
              Intelligence Marketplace
            </span>
            <span className="rounded bg-accent/20 px-2 py-0.5 text-xs font-medium text-accent">
              Research Agent
            </span>
          </div>
          <a
            href={STREAMLIT_APP_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-gray-400 hover:text-accent"
          >
            Streamlit app →
          </a>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
        {/* Top: Metaplex details */}
        <div className="mb-10">
          <h1 className="text-2xl font-bold text-white sm:text-3xl">
            Metaplex Agent
          </h1>
          <p className="mt-2 text-gray-400">
            On-chain identity and token. Run the agent below.
          </p>
          <div className="mt-6 grid gap-6 sm:grid-cols-2">
            <AgentIdentity />
            <RaaTokenSection />
          </div>
        </div>

        {/* Run agent */}
        <div>
          <h2 className="mb-2 text-xl font-semibold text-white">
            Run the agent
          </h2>
          <p className="mb-6 text-sm text-gray-400">
            Same flow as the Streamlit app: goal → plan and quote → pay on
            Solana (devnet) → run continues automatically when payment is
            detected → plan and answer.
          </p>
          <RunAgent />
        </div>

        <footer className="mt-16 border-t border-border pt-8 text-center text-sm text-gray-500">
          <a
            href="https://www.metaplex.com/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="text-accent hover:underline"
          >
            Metaplex Developer Hub
          </a>
          {" · "}
          <a
            href="https://developers.metaplex.com/agents"
            target="_blank"
            rel="noopener noreferrer"
            className="text-accent hover:underline"
          >
            Metaplex Agents
          </a>
        </footer>
      </main>
    </div>
  );
}
