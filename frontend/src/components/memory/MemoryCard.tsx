import type { MemoryItem } from "../../types";

interface MemoryCardProps {
  item: MemoryItem;
}

export function MemoryCard({ item }: MemoryCardProps) {
  return (
    <article className="card memory-card">
      <h4>{item.type}</h4>
      <p>{item.content}</p>
      <div className="memory-meta">
        <span>{item.owner}</span>
        <span>{new Date(item.createdAt).toLocaleString()}</span>
        <span>{Math.round(item.confidence * 100)}%</span>
      </div>
    </article>
  );
}
