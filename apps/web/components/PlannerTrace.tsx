import { StatusBadge } from "./StatusBadge";


export function PlannerTrace({ plannerRun, traceEvents }: { plannerRun: any; traceEvents: any[] }) {
  return (
    <div className="panel">
      <h2>Planner Agent Trace</h2>
      <div className="meta">
        <StatusBadge label={plannerRun.planner_status} />
        <StatusBadge label={plannerRun.current_step} />
        {plannerRun.selected_workers.map((worker: string) => (
          <StatusBadge key={worker} label={worker} />
        ))}
      </div>
      <p>{plannerRun.rationale_summary}</p>
      <p>
        <strong>Decision log:</strong> {plannerRun.decision_log.join(" ")}
      </p>
      <div className="trace-list">
        {traceEvents.map((event: any) => (
          <article className="trace-event" key={event.id}>
            <div className="meta">
              <StatusBadge label={event.event_type} />
              {event.task_id ? <span>Task {event.task_id}</span> : <span>Planner scope</span>}
            </div>
            <h3>{event.title}</h3>
            <p className="trace-detail">{event.detail}</p>
            <small>{event.created_at}</small>
          </article>
        ))}
      </div>
    </div>
  );
}
