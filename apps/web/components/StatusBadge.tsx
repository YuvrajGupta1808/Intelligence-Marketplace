export function StatusBadge({ label }: { label: string }) {
  return <span className="badge">{label.replaceAll("_", " ")}</span>;
}

