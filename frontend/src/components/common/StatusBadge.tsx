interface StatusBadgeProps {
  status: "running" | "stopped" | "starting" | "stopping";
}

export function StatusBadge({ status }: StatusBadgeProps) {
  return <span className={`status-badge status-${status}`}>{status.toUpperCase()}</span>;
}
