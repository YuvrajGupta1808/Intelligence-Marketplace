"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { runAgent, explorerTxUrl } from "@/lib/api";
import type { RunResult } from "@/lib/api";

const NETWORK = process.env.NEXT_PUBLIC_NETWORK || "devnet";
const POLL_INTERVAL_MS = 5000;

export default function RunAgent() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RunResult | null>(null);
  const [polling, setPolling] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const paymentRequired =
    result?.kind === "payment_required" ? result.data : null;
  const success = result?.kind === "success" ? result.data : null;
  const error = result?.kind === "error" ? result : null;

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    setPolling(false);
  }, []);

  async function handleRun() {
    if (!query.trim()) return;
    setLoading(true);
    setResult(null);
    stopPolling();
    try {
      const res = await runAgent(query);
      setResult(res);
      if (res.kind === "payment_required") {
        setPolling(true);
        pollRef.current = setInterval(async () => {
          const next = await runAgent(query);
          setResult(next);
          if (next.kind === "success") stopPolling();
        }, POLL_INTERVAL_MS);
      }
    } catch (e) {
      setResult({
        kind: "error",
        status: 0,
        message: e instanceof Error ? e.message : "Request failed",
      });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => () => stopPolling(), [stopPolling]);

  return (
    <section className="rounded-xl border border-border bg-surface-elevated p-6">
      <h2 className="mb-1 text-lg font-semibold text-white">
        Run research agent
      </h2>
      <p className="mb-4 text-sm text-gray-400">
        Enter a goal; agent returns a plan and quote. Send the payment — the
        run continues automatically when payment is detected.
      </p>

      <textarea
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="e.g. What are the main causes of climate change and one recent EU policy?"
        className="mb-4 w-full resize-y rounded-lg border border-border bg-surface px-4 py-3 text-gray-100 placeholder-gray-500 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent/50"
        rows={3}
        disabled={loading || polling}
      />

      {!paymentRequired && !success && (
        <button
          onClick={() => handleRun()}
          disabled={loading || !query.trim()}
          className="rounded-lg bg-accent px-4 py-2.5 font-medium text-surface hover:bg-accent-muted disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Getting quote…" : "Get quote & run"}
        </button>
      )}

      {paymentRequired && (
        <div className="space-y-4 rounded-lg border border-amber-500/30 bg-amber-500/5 p-4">
          {paymentRequired.plan && paymentRequired.plan.length > 0 && (
            <div>
              <h3 className="mb-2 text-sm font-medium text-gray-400">Plan</h3>
              <ol className="list-inside list-decimal space-y-1 text-sm text-gray-300">
                {paymentRequired.plan.map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ol>
            </div>
          )}
          <h3 className="text-sm font-medium text-amber-200">Quote</h3>
          <p className="text-sm text-gray-300">
            Pay{" "}
            <strong className="text-white">
              {paymentRequired.quote_sol} SOL
            </strong>{" "}
            to <code className="rounded bg-surface px-1 font-mono text-xs">{paymentRequired.receiver}</code>{" "}
            (devnet). The run will continue automatically when payment is
            detected (no need to click Run again).
          </p>
          {polling && (
            <p className="flex items-center gap-2 text-sm text-gray-400">
              <span className="h-2 w-2 animate-pulse rounded-full bg-accent" />
              Checking for payment every {POLL_INTERVAL_MS / 1000}s (up to ~5 min)…
            </p>
          )}
          <button
            onClick={() => {
              stopPolling();
              setResult(null);
            }}
            className="rounded-lg border border-border px-4 py-2.5 text-gray-300 hover:bg-surface-overlay"
          >
            Cancel
          </button>
        </div>
      )}

      {success && (
        <div className="mt-4 space-y-4">
          {success.plan.length > 0 && (
            <div>
              <h3 className="mb-2 text-sm font-medium text-gray-400">Plan</h3>
              <ol className="list-inside list-decimal space-y-1 text-sm text-gray-300">
                {success.plan.map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ol>
            </div>
          )}
          <div>
            <h3 className="mb-2 text-sm font-medium text-gray-400">
              Final answer
            </h3>
            <div className="rounded-lg border border-border bg-surface p-4 text-gray-200 [&_h1]:text-lg [&_h1]:font-bold [&_h1]:mt-4 [&_h1]:mb-2 [&_h2]:text-base [&_h2]:font-semibold [&_h2]:mt-3 [&_h2]:mb-2 [&_h3]:text-sm [&_h3]:font-semibold [&_h3]:mt-2 [&_h3]:mb-1 [&_p]:mb-2 [&_ul]:list-disc [&_ul]:list-inside [&_ul]:mb-2 [&_ul]:space-y-1 [&_ol]:list-decimal [&_ol]:list-inside [&_ol]:mb-2 [&_ol]:space-y-1 [&_strong]:font-semibold">
              <ReactMarkdown>{success.final_answer || "—"}</ReactMarkdown>
            </div>
          </div>
          {success.tool_call_log.length > 0 && (
            <div>
              <h3 className="mb-2 text-sm font-medium text-gray-400">
                Tool payments (on-chain)
              </h3>
              <ul className="space-y-2">
                {success.tool_call_log.map((entry, i) => (
                  <li
                    key={i}
                    className="flex flex-wrap items-center gap-2 text-sm"
                  >
                    <span className="text-gray-400">
                      {entry.tool ?? "—"}:{" "}
                      {((entry.amount_lamports ?? 0) / 1e9).toFixed(6)} SOL
                    </span>
                    {entry.tx &&
                      entry.tx !== "simulated" &&
                      entry.tx !== "failed" && (
                        <a
                          href={explorerTxUrl(entry.tx, NETWORK)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-accent hover:underline"
                        >
                          View tx →
                        </a>
                      )}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <button
            onClick={() => setResult(null)}
            className="rounded-lg border border-border px-4 py-2 text-sm text-gray-300 hover:bg-surface-overlay"
          >
            New query
          </button>
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-200">
          <p>
            Error {error.status ? `(${error.status})` : ""}: {error.message}
          </p>
          <button
            onClick={() => setResult(null)}
            className="mt-2 text-red-300 underline hover:no-underline"
          >
            Dismiss
          </button>
        </div>
      )}
    </section>
  );
}
