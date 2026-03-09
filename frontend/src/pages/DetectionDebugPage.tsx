import { useMemo, useState } from "react";
import { useDetectionsLatestQuery } from "../api/hooks";
import { DetectionImagePanel } from "../components/detection/DetectionImagePanel";
import { DetectionTable } from "../components/detection/DetectionTable";
import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { StatCard } from "../components/dashboard/StatCard";
import type { DetectionResult } from "../types";

const labels: Array<DetectionResult["label"] | "all"> = [
  "all",
  "bubble_other",
  "bubble_me",
  "timestamp",
  "system_tip",
];

export function DetectionDebugPage() {
  const { data, isLoading, isError, error } = useDetectionsLatestQuery();
  const [labelFilter, setLabelFilter] = useState<(typeof labels)[number]>("all");
  const [minConfidence, setMinConfidence] = useState(0);
  const [selectedId, setSelectedId] = useState<string | undefined>(undefined);

  const filteredRows = useMemo(() => {
    if (!data) return [];
    return data.detections.filter((row) => {
      const passLabel = labelFilter === "all" || row.label === labelFilter;
      const passConfidence = row.confidence >= minConfidence;
      return passLabel && passConfidence;
    });
  }, [data, labelFilter, minConfidence]);

  const selected = filteredRows.find((row) => row.id === selectedId) ?? filteredRows[0];

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState message={error.message} />;
  if (!data) return <ErrorState message="No detection data" />;

  return (
    <section className="page-grid">
      <div className="mini-stats-grid">
        <StatCard title="Detections" value={data.detections.length} />
        <StatCard title="Filtered" value={filteredRows.length} />
        <StatCard title="Selected Label" value={selected?.label ?? "-"} />
        <StatCard
          title="Selected Confidence"
          value={selected ? `${Math.round(selected.confidence * 100)}%` : "-"}
        />
      </div>

      <div className="card filter-row">
        <label>
          Label
          <select
            value={labelFilter}
            onChange={(e) => setLabelFilter(e.target.value as (typeof labels)[number])}
          >
            {labels.map((label) => (
              <option key={label} value={label}>
                {label}
              </option>
            ))}
          </select>
        </label>

        <label>
          Min Confidence ({Math.round(minConfidence * 100)}%)
          <input
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={minConfidence}
            onChange={(e) => setMinConfidence(Number(e.target.value))}
          />
        </label>
      </div>

      <DetectionImagePanel imageUrl={data.imageUrl} capturedAt={data.capturedAt} />
      <DetectionTable rows={filteredRows} selectedId={selected?.id} onSelect={setSelectedId} />
    </section>
  );
}
