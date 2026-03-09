import type { ChatMessage } from "../../types";

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  return (
    <article className={`message-bubble role-${message.senderRole}`}>
      <div className="message-text">{message.text}</div>
      <div className="message-meta">
        <span>{message.senderRole}</span>
        <span>{new Date(message.timestamp).toLocaleTimeString()}</span>
        <span>{Math.round(message.confidence * 100)}%</span>
      </div>
    </article>
  );
}
