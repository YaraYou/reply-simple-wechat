import type { LogItem } from "../../types";

interface LogViewerProps {
  logs: LogItem[];
}

export function LogViewer({ logs }: LogViewerProps) {
  return (
    <section className="card log-viewer">
      <h3>Logs</h3>
      <div className="log-list">
        {logs.map((log) => (
          <div key={log.id} className={`log-row log-${log.level.toLowerCase()}`}>
            <span>{new Date(log.timestamp).toLocaleTimeString()}</span>
            <span>{log.level}</span>
            <span>{log.message}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
