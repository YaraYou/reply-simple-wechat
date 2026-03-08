// app/messages/page.tsx
"use client";

import { useEffect, useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

interface Message {
  id: number;
  sender: string;
  content: string;
  intent: string;
  reply: string;
  time: string;
}

export default function MessagesPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/messages")
      .then(res => res.json())
      .then(data => {
        setMessages(data.messages);
        setLoading(false);
      });
  }, []);

  const intentColor = (intent: string) => {
    const colors: Record<string, string> = {
      greeting: "bg-green-100 text-green-800",
      task: "bg-blue-100 text-blue-800",
      question: "bg-yellow-100 text-yellow-800",
      feedback: "bg-purple-100 text-purple-800",
      general: "bg-gray-100 text-gray-800",
    };
    return colors[intent] || "bg-gray-100 text-gray-800";
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">消息日志</h1>

      {loading ? (
        <div>加载中...</div>
      ) : (
        <div className="border rounded-lg">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>发送者</TableHead>
                <TableHead>消息内容</TableHead>
                <TableHead>意图</TableHead>
                <TableHead>回复内容</TableHead>
                <TableHead>时间</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {messages.map((msg) => (
                <TableRow key={msg.id}>
                  <TableCell className="font-medium">{msg.sender}</TableCell>
                  <TableCell>{msg.content}</TableCell>
                  <TableCell>
                    <Badge className={intentColor(msg.intent)}>
                      {msg.intent}
                    </Badge>
                  </TableCell>
                  <TableCell>{msg.reply}</TableCell>
                  <TableCell>{msg.time}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}