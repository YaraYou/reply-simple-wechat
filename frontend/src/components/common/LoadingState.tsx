import type { PropsWithChildren } from "react";

export function LoadingState({ children }: PropsWithChildren) {
  return <div className="state state-loading">{children ?? "Loading..."}</div>;
}
