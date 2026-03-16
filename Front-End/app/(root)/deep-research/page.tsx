"use client";

import { FormEvent, useState } from "react";
import ReactMarkdown from "react-markdown";

type StepResult = {
  step_index: number;
  result: string;
};

type ToolPaymentEntry = {
  tool?: string;
  amount_lamports?: number;
  tx?: string;
};

const CHAT_API_BASE =
  process.env.NEXT_PUBLIC_CHAT_API_URL || "http://localhost:7001";

const METAPLEX_AGENT_ASSET =
  process.env.NEXT_PUBLIC_AGENT_ASSET ||
  "GNdop5oApBkRfH5YDZPDkVKBudENNwaXLmykEg6U5Gmm";
const METAPLEX_OPERATIONAL_WALLET =
  process.env.NEXT_PUBLIC_OPERATIONAL_WALLET ||
  "6rmVGBrJrvQaJnBFKBaFSKGZv4DnTHEoe1H1TVa6zaYU";
const METAPLEX_NETWORK =
  process.env.NEXT_PUBLIC_NETWORK || "devnet";
const METAPLEX_GENESIS_URL =
  process.env.NEXT_PUBLIC_GENESIS_LAUNCH_URL ||
  "https://www.metaplex.com/token/UKBsjo8vkazhyhyrjJUr2SBrCzvybKQd73k9fJaPLEX?network=solana-devnet";

export default function DeepResearchPage() {
  const [query, setQuery] = useState("Analyze AAPL as a long-term investment.");
  const [isRunning, setIsRunning] = useState(false);
  const [plan, setPlan] = useState<string[]>([]);
  const [quote, setQuote] = useState<{
    quote_lamports?: number;
    quote_sol?: number;
    receiver?: string;
    network?: string;
  }>({});
  const [steps, setSteps] = useState<StepResult[]>([]);
  const [finalAnswer, setFinalAnswer] = useState<string>("");
  const [toolCallLog, setToolCallLog] = useState<ToolPaymentEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isRunning) return;

    setIsRunning(true);
    setError(null);
    setPlan([]);
    setQuote({});
    setSteps([]);
    setFinalAnswer("");
    setToolCallLog([]);

    const url = `${CHAT_API_BASE}/chat/stream-get?query=${encodeURIComponent(
      query.trim()
    )}`;
    const es = new EventSource(url);

    es.addEventListener("planner", (ev: MessageEvent) => {
      try {
        const data = JSON.parse(ev.data);
        if (Array.isArray(data.plan)) setPlan(data.plan);
      } catch {
        // ignore parse errors
      }
    });

    es.addEventListener("quote", (ev: MessageEvent) => {
      try {
        const data = JSON.parse(ev.data);
        setQuote(data);
      } catch {
        // ignore
      }
    });

    es.addEventListener("step", (ev: MessageEvent) => {
      try {
        const data: StepResult = JSON.parse(ev.data);
        setSteps((prev) => [...prev, data]);
      } catch {
        // ignore
      }
    });

    es.addEventListener("final_answer", (ev: MessageEvent) => {
      try {
        const data = JSON.parse(ev.data);
        if (typeof data.final_answer === "string") {
          setFinalAnswer(data.final_answer);
        }
      } catch {
        // ignore
      }
    });

    es.addEventListener("tool_payments", (ev: MessageEvent) => {
      try {
        const data = JSON.parse(ev.data);
        if (Array.isArray(data.tool_call_log)) {
          setToolCallLog(data.tool_call_log);
        }
      } catch {
        // ignore
      }
    });

    es.addEventListener("done", () => {
      es.close();
      setIsRunning(false);
    });

    es.onerror = () => {
      es.close();
      setIsRunning(false);
      setError("Streaming failed. Check that chat_api is running.");
    };
  };

  return (
    <section className="mx-auto flex max-w-5xl flex-col gap-6 px-4 pb-12 pt-6 md:px-8">
      <header className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div className="space-y-2">
          <h1 className="text-2xl font-semibold text-gray-100">
            Deep Research with Metaplex
          </h1>
          <p className="text-gray-400 text-sm">
            Streams plan, quote, step results, and the final synthesized answer
            from the on-chain registered Metaplex agent.
          </p>
        </div>

        <aside className="w-full max-w-md rounded-lg border border-gray-800 bg-gray-950 px-4 py-3 text-xs text-gray-300 shadow-md">
          <div className="flex items-center justify-between gap-2">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-gray-400">
              Metaplex Agent Registry
            </p>
            <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-[11px] font-medium text-emerald-400">
              {METAPLEX_NETWORK}
            </span>
          </div>
          <dl className="mt-2 space-y-1.5">
            <div className="flex flex-col">
              <dt className="text-[11px] font-medium text-gray-500">
                Agent asset
              </dt>
              <dd className="font-mono text-[11px] break-all text-emerald-300">
                {METAPLEX_AGENT_ASSET}
              </dd>
            </div>
            <div className="flex flex-col">
              <dt className="text-[11px] font-medium text-gray-500">
                Operational wallet
              </dt>
              <dd className="font-mono text-[11px] break-all text-sky-300">
                {METAPLEX_OPERATIONAL_WALLET}
              </dd>
            </div>
            <div className="flex flex-col">
              <dt className="text-[11px] font-medium text-gray-500">
                Genesis RAA launch
              </dt>
              <dd>
                <a
                  href={METAPLEX_GENESIS_URL}
                  target="_blank"
                  rel="noreferrer"
                  className="text-[11px] text-indigo-300 underline-offset-2 hover:text-indigo-200 hover:underline"
                >
                  Open launch page
                </a>
              </dd>
            </div>
          </dl>
        </aside>
      </header>

      <form onSubmit={handleSubmit} className="space-y-3 rounded-lg border border-gray-800 bg-gray-950/60 p-4">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          rows={3}
          className="w-full rounded-md bg-gray-900 border border-gray-700 px-3 py-2 text-sm text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Describe the stock or company research you want..."
        />
        <button
          type="submit"
          disabled={isRunning || !query.trim()}
          className="inline-flex items-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50"
        >
          {isRunning ? "Running..." : "Run Deep Research"}
        </button>
        {error && <p className="text-sm text-red-400">{error}</p>}
      </form>

      {plan.length > 0 && (
        <div className="rounded-lg border border-gray-800 bg-gray-950/80 p-4 space-y-2">
          <h2 className="text-sm font-semibold text-gray-200">Plan</h2>
          <ol className="list-decimal list-inside text-sm text-gray-300 space-y-1">
            {plan.map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ol>
        </div>
      )}

      {(quote.quote_sol || quote.receiver) && (
        <div className="rounded-lg border border-gray-800 bg-gray-950/80 p-4 space-y-1 text-sm text-gray-300">
          <h2 className="text-sm font-semibold text-gray-200">Quote</h2>
          {typeof quote.quote_sol === "number" && (
            <p>
              <span className="font-semibold">Price:</span>{" "}
              {quote.quote_sol.toFixed(6)} SOL
            </p>
          )}
          {quote.receiver && (
            <p>
              <span className="font-semibold">Receiver:</span> {quote.receiver} (
              {quote.network})
            </p>
          )}
        </div>
      )}

      {steps.length > 0 && (
        <div className="rounded-lg border border-gray-800 bg-gray-950/80 p-4 space-y-2">
          <h2 className="text-sm font-semibold text-gray-200">Step results</h2>
          <div className="space-y-2">
            {steps.map((s) => (
              <details
                key={s.step_index}
                className="rounded border border-gray-800 bg-black/40 p-2"
                open={s.step_index === steps.length - 1}
              >
                <summary className="cursor-pointer text-sm text-gray-200">
                  Step {s.step_index + 1}
                </summary>
                <pre className="mt-1 whitespace-pre-wrap text-xs text-gray-300">
                  {s.result}
                </pre>
              </details>
            ))}
          </div>
        </div>
      )}

      {finalAnswer && (
        <div className="rounded-lg border border-gray-800 bg-gray-950/80 p-4 space-y-3">
          <h2 className="text-sm font-semibold text-gray-200">Final answer</h2>
          <div className="final-answer-markdown text-sm text-gray-300 [&_h1]:text-lg [&_h1]:font-bold [&_h1]:text-gray-100 [&_h1]:mt-4 [&_h1]:mb-2 [&_h2]:text-base [&_h2]:font-semibold [&_h2]:text-gray-200 [&_h2]:mt-3 [&_h2]:mb-2 [&_h3]:text-sm [&_h3]:font-semibold [&_h3]:text-gray-200 [&_h3]:mt-2 [&_h3]:mb-1 [&_p]:mb-2 [&_ul]:list-disc [&_ul]:list-inside [&_ul]:mb-2 [&_ul]:space-y-1 [&_ol]:list-decimal [&_ol]:list-inside [&_ol]:mb-2 [&_ol]:space-y-1 [&_strong]:font-semibold [&_strong]:text-gray-200">
            <ReactMarkdown>{finalAnswer}</ReactMarkdown>
          </div>
        </div>
      )}

      {toolCallLog.length > 0 && (
        <div className="rounded-lg border border-gray-800 bg-gray-950/80 p-4 space-y-2">
          <h2 className="text-sm font-semibold text-gray-200">
            Tool payments (on-chain)
          </h2>
          <ul className="list-disc list-inside space-y-1 text-sm text-gray-300">
            {toolCallLog.map((entry, i) => {
              const tool = entry.tool ?? "—";
              const lamports = entry.amount_lamports ?? 0;
              const sol = (lamports / 1e9).toFixed(6);
              const tx = entry.tx ?? "";
              const showTxLink =
                tx && tx !== "simulated" && tx !== "failed";
              const explorerUrl = `https://explorer.solana.com/tx/${tx}?cluster=${METAPLEX_NETWORK}`;
              return (
                <li key={i}>
                  <span className="font-medium text-gray-200">{tool}</span>:{" "}
                  {sol} SOL
                  {showTxLink ? (
                    <>
                      {" "}
                      —{" "}
                      <a
                        href={explorerUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 underline"
                      >
                        View transaction
                      </a>
                    </>
                  ) : (
                    tx && ` — ${tx}`
                  )}
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </section>
  );
}

