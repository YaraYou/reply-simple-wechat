interface ErrorStateProps {
  message?: string;
}

export function ErrorState({ message }: ErrorStateProps) {
  return <div className="state state-error">{message ?? "Request failed"}</div>;
}
