import { useMemoriesQuery } from "../api/hooks";
import { EmptyState } from "../components/common/EmptyState";
import { ErrorState } from "../components/common/ErrorState";
import { LoadingState } from "../components/common/LoadingState";
import { MemoryCard } from "../components/memory/MemoryCard";

export function MemoryCenterPage() {
  const { data, isLoading, isError, error } = useMemoriesQuery();

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState message={error.message} />;
  if (!data?.length) return <EmptyState>暂无记忆项</EmptyState>;

  return (
    <section className="page-grid">
      {data.map((item) => (
        <MemoryCard key={item.id} item={item} />
      ))}
    </section>
  );
}
