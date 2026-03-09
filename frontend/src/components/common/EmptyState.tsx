import type { PropsWithChildren } from "react";

export function EmptyState({ children }: PropsWithChildren) {
  return <div className="state state-empty">{children ?? "No data"}</div>;
}
