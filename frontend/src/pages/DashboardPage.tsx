import { useMemo } from "react";
import { useStatusQuery } from "../api/hooks";
import { ReplyPreviewCard } from "../components/chat/ReplyPreviewCard";
import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { StatusBadge } from "../components/common/StatusBadge";
import { StatCard } from "../components/dashboard/StatCard";

const formatDuration = (seconds: number): string => {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}h ${m}m ${s}s`;
  return `${m}m ${s}s`;
};

export function DashboardPage() {
  const { data, isLoading, isError, error } = useStatusQuery();

  const latestMessageAt = useMemo(
    () => (data ? new Date(data.latestMessageAt).toLocaleString() : "-"),
    [data],
  );

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState message={error.message} />;
  if (!data) return <ErrorState message="No status data" />;

  return (
    <section className="page-grid two-col">
      <StatCard title="Bot State" value={<StatusBadge status={data.state} />} />
      <StatCard title="Analyzer Mode" value={data.analyzerMode} hint="rule / ml" />
      <StatCard
        title="Detector"
        value={data.detectorEnabled ? "YOLO + OCR Enabled" : "Fallback OCR"}
      />
      <StatCard title="Queue Depth" value={data.queueDepth} />
      <StatCard title="Latest Message" value={latestMessageAt} />
      <StatCard title="Uptime" value={formatDuration(data.uptimeSeconds)} />
      <ReplyPreviewCard preview="候选回复将在 Chat Monitor 页面展示" />
    </section>
  );
}
