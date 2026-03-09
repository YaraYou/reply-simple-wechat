import { useStatusQuery, useStartMutation, useStopMutation } from "../../api/hooks";
import { apiConfig } from "../../api/config";
import { StatusBadge } from "../common/StatusBadge";

export function Topbar() {
  const statusQuery = useStatusQuery();
  const startMutation = useStartMutation();
  const stopMutation = useStopMutation();

  const modeText = apiConfig.useMock ? "MOCK" : "REAL";
  const healthText = apiConfig.useMock
    ? "Mock Data"
    : statusQuery.isError
      ? "Disconnected"
      : statusQuery.isLoading
        ? "Checking"
        : "Connected";

  const healthClass = apiConfig.useMock
    ? "health-mock"
    : statusQuery.isError
      ? "health-down"
      : statusQuery.isLoading
        ? "health-checking"
        : "health-up";

  return (
    <header className="topbar">
      <div className="topbar-title">
        <span>微信个人助手控制台</span>
        {statusQuery.data ? <StatusBadge status={statusQuery.data.state} /> : null}
        <span className="api-mode-badge">{modeText}</span>
        <span className={`api-health-badge ${healthClass}`}>{healthText}</span>
      </div>
      <div className="topbar-actions">
        <button
          type="button"
          onClick={() => startMutation.mutate()}
          disabled={startMutation.isPending}
        >
          Start
        </button>
        <button
          type="button"
          onClick={() => stopMutation.mutate()}
          disabled={stopMutation.isPending}
        >
          Stop
        </button>
      </div>
    </header>
  );
}
