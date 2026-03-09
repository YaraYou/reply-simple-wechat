import type { CurrentContext } from "../../types";

interface ContextPanelProps {
  context: CurrentContext;
}

export function ContextPanel({ context }: ContextPanelProps) {
  return (
    <section className="card context-panel">
      <h3>Current Context</h3>
      <div className="context-meta-row">
        <span>Chat Key</span>
        <strong>{context.chatKey}</strong>
      </div>
      <div className="context-meta-row">
        <span>Recent Count</span>
        <strong>{context.recentMessages.length}</strong>
      </div>
      <div className="context-candidate">
        <span>Reply Candidate</span>
        <p>{context.replyCandidate ? context.replyCandidate.text : "None"}</p>
      </div>
      <div className="context-timeline">
        <h4>Context Timeline</h4>
        {context.recentMessages.slice(-5).map((msg) => (
          <div key={msg.id} className="context-line">
            <span>{msg.senderRole}</span>
            <span>{new Date(msg.timestamp).toLocaleTimeString()}</span>
            <span className="context-text">{msg.text}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
