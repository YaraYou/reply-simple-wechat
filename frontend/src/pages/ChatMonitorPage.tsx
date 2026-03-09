import { useMemo } from "react";
import { useCurrentContextQuery, useRecentMessagesQuery } from "../api/hooks";
import { ContextPanel } from "../components/chat/ContextPanel";
import { MessageList } from "../components/chat/MessageList";
import { ReplyPreviewCard } from "../components/chat/ReplyPreviewCard";
import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { StatCard } from "../components/dashboard/StatCard";

export function ChatMonitorPage() {
  const messagesQuery = useRecentMessagesQuery();
  const contextQuery = useCurrentContextQuery();

  const stats = useMemo(() => {
    const messages = messagesQuery.data ?? [];
    const byRole = {
      me: messages.filter((m) => m.senderRole === "me").length,
      other: messages.filter((m) => m.senderRole === "other").length,
      system: messages.filter((m) => m.senderRole === "system").length,
    };
    const lowConfidence = messages.filter((m) => m.confidence < 0.8).length;
    const latestSource = messages.length ? messages[messages.length - 1].source : "-";
    return { byRole, lowConfidence, latestSource };
  }, [messagesQuery.data]);

  if (messagesQuery.isLoading || contextQuery.isLoading) return <LoadingState />;
  if (messagesQuery.isError) return <ErrorState message={messagesQuery.error.message} />;
  if (contextQuery.isError) return <ErrorState message={contextQuery.error.message} />;
  if (!messagesQuery.data || !contextQuery.data) return <ErrorState message="No chat data" />;

  return (
    <section className="page-grid">
      <div className="mini-stats-grid">
        <StatCard title="Other Messages" value={stats.byRole.other} />
        <StatCard title="Me Messages" value={stats.byRole.me} />
        <StatCard title="System Messages" value={stats.byRole.system} />
        <StatCard title="Low Confidence" value={stats.lowConfidence} />
        <StatCard title="Latest Parse Source" value={stats.latestSource} />
      </div>

      <div className="page-grid two-col">
        <MessageList messages={messagesQuery.data} />
        <ContextPanel context={contextQuery.data} />
      </div>

      <ReplyPreviewCard preview={contextQuery.data.replyCandidate?.text} />
    </section>
  );
}
