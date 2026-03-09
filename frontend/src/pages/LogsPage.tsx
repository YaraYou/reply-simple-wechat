import { useMemo, useState } from "react";
import { useLogsQuery } from "../api/hooks";
import { EmptyState } from "../components/common/EmptyState";
import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { LogViewer } from "../components/logs/LogViewer";
import type { LogItem } from "../types";

type LevelFilter = LogItem["level"] | "ALL";

const levels: LevelFilter[] = ["ALL", "DEBUG", "INFO", "WARNING", "ERROR"];

export function LogsPage() {
  const { data, isLoading, isError, error } = useLogsQuery();
  const [levelFilter, setLevelFilter] = useState<LevelFilter>("ALL");
  const [keyword, setKeyword] = useState("");

  const filtered = useMemo(() => {
    const logs = data ?? [];
    return logs.filter((log) => {
      const passLevel = levelFilter === "ALL" || log.level === levelFilter;
      const passKeyword = keyword.trim().length === 0 || log.message.toLowerCase().includes(keyword.toLowerCase());
      return passLevel && passKeyword;
    });
  }, [data, keyword, levelFilter]);

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState message={error.message} />;
  if (!data?.length) return <EmptyState>暂无日志</EmptyState>;

  return (
    <section className="page-grid">
      <div className="card filter-row">
        <label>
          Level
          <select value={levelFilter} onChange={(e) => setLevelFilter(e.target.value as LevelFilter)}>
            {levels.map((lvl) => (
              <option key={lvl} value={lvl}>
                {lvl}
              </option>
            ))}
          </select>
        </label>

        <label>
          Keyword
          <input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="search message"
          />
        </label>

        <div className="log-count">Matched: {filtered.length}</div>
      </div>

      {filtered.length ? <LogViewer logs={filtered} /> : <EmptyState>当前筛选条件下无日志</EmptyState>}
    </section>
  );
}
