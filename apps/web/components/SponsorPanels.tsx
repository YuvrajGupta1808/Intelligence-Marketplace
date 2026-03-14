import { StatusBadge } from "./StatusBadge";


function paymentEvents(traceEvents: any[]) {
  return traceEvents.filter((event) => event.event_type === "payment_settled");
}

function fundedEvents(events: any[]) {
  return events.filter((event) => event.event_type === "funded");
}

export function SponsorPanels({ job }: { job: any }) {
  const payments = paymentEvents(job.trace_events);
  const funded = fundedEvents(job.settlement_events);

  return (
    <section className="three-column">
      <div className="panel">
        <h2>Unbrowse</h2>
        <div className="sponsor-list">
          {job.execution_results.map((result: any) => (
            <article key={result.task_id} className="trace-event">
              <div className="meta">
                <StatusBadge label={result.provider} />
                {result.provider_status ? <StatusBadge label={result.provider_status} /> : null}
              </div>
              <p>Run ID: {result.provider_run_id || "n/a"}</p>
              <p>Final URL: {result.final_url}</p>
              <p>Skill ID: {result.provider_metadata?.skill_id || "n/a"}</p>
            </article>
          ))}
        </div>
      </div>

      <div className="panel">
        <h2>x402 / Solana</h2>
        <div className="sponsor-list">
          {payments.length ? payments.map((event: any) => (
            <article key={event.id} className="trace-event">
              <div className="meta">
                <StatusBadge label={event.metadata.payment_mode || "real"} />
                <StatusBadge label={String(event.metadata.network || "solana-devnet")} />
              </div>
              <p>Asset: {String(event.metadata.asset || "USDC")}</p>
              <p>Facilitator: {String(event.metadata.facilitator_url || "n/a")}</p>
              <p>Payment response: {event.metadata.payment_response_header ? "present" : "missing"}</p>
            </article>
          )) : <p>No payment settlement trace yet.</p>}
        </div>
      </div>

      <div className="panel">
        <h2>Arkhai / Alkahest</h2>
        <div className="sponsor-list">
          {funded.length ? funded.map((event: any) => (
            <article key={`${event.task_id}-${event.timestamp}`} className="trace-event">
              <div className="meta">
                <StatusBadge label={String(event.metadata.settlement_mode || "app")} />
                {event.metadata.chain_name ? <StatusBadge label={String(event.metadata.chain_name)} /> : null}
              </div>
              <p>Escrow UID: {event.metadata.escrow_uid || event.metadata.escrow_id || "n/a"}</p>
              <p>Fund tx: {event.metadata.fund_tx_hash || "n/a"}</p>
              <p>Arbiter: {event.metadata.arbiter_contract || "n/a"}</p>
            </article>
          )) : <p>No escrow events yet.</p>}
        </div>
      </div>
    </section>
  );
}
