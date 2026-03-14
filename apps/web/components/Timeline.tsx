import { StatusBadge } from "./StatusBadge";


export function Timeline({ events }: { events: any[] }) {
  return (
    <div className="timeline">
      {events.map((event) => (
        <div className="timeline-event panel" key={`${event.task_id}-${event.event_type}-${event.timestamp}`}>
          <div className="meta">
            <StatusBadge label={event.event_type} />
            <span>{event.amount_usdc} USDC</span>
            {event.metadata?.settlement_mode ? <StatusBadge label={event.metadata.settlement_mode} /> : null}
          </div>
          <div>{event.timestamp}</div>
          <div>Task: {event.task_id}</div>
          {event.metadata?.fund_tx_hash ? <div>Fund tx: {event.metadata.fund_tx_hash}</div> : null}
          {event.metadata?.collect_tx_hash ? <div>Collect tx: {event.metadata.collect_tx_hash}</div> : null}
          {event.metadata?.reclaim_tx_hash ? <div>Reclaim tx: {event.metadata.reclaim_tx_hash}</div> : null}
        </div>
      ))}
    </div>
  );
}
