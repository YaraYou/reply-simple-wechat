import type { ChatMessage } from "../../types";
import { EmptyState } from "../common/EmptyState";
import { MessageBubble } from "./MessageBubble";

interface MessageListProps {
  messages: ChatMessage[];
}

export function MessageList({ messages }: MessageListProps) {
  if (!messages.length) {
    return <EmptyState>暂无消息</EmptyState>;
  }

  return (
    <section className="message-list">
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}
    </section>
  );
}
