import { StatusBadge } from "./StatusBadge";


export function TaskBoard({ job }: { job: any }) {
  const quotesByTask = new Map<string, any>(job.quotes.map((quote: any) => [quote.task_id, quote]));
  const resultsByTask = new Map<string, any>(job.execution_results.map((result: any) => [result.task_id, result]));
  const verificationsByTask = new Map<string, any>(job.verification_results.map((result: any) => [result.task_id, result]));

  return (
    <div className="task-list">
      {job.tasks.map((task: any) => {
        const quote: any = quotesByTask.get(task.id);
        const result: any = resultsByTask.get(task.id);
        const verification: any = verificationsByTask.get(task.id);
        return (
          <article className="task" key={task.id}>
            <div className="meta">
              <StatusBadge label={task.status} />
              {quote ? <StatusBadge label={`quote ${quote.price_usdc} usdc`} /> : null}
              {verification ? <StatusBadge label={verification.passed ? "verified" : "refunded"} /> : null}
            </div>
            <h3>{task.target_url}</h3>
            <p>Allowed domain: {task.allowed_domain}</p>
            {result ? (
              <>
                <div className="meta">
                  <StatusBadge label={result.provider} />
                  {result.provider_status ? <StatusBadge label={result.provider_status} /> : null}
                </div>
                <p>
                  Extracted: <strong>{result.plan_name}</strong> at <strong>{result.price_found}</strong>
                </p>
                <p>{result.evidence.excerpt}</p>
                <img className="artifact" src={result.evidence.screenshot_url} alt={`${task.allowed_domain} evidence`} />
              </>
            ) : (
              <p>Awaiting execution.</p>
            )}
          </article>
        );
      })}
    </div>
  );
}
