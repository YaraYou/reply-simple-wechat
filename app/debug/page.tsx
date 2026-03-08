// app/debug/page.tsx
"use client";

import { AssistantRuntimeProvider, useAssistantRuntime, useThread, useThreadListItem, useThreads, useTool } from "assistant-ui";
import { makeAssistantTool, useLocalRuntime } from "assistant-ui/react";
import { Button } from "@/components/ui/button";
import {
  Composer,
  Thread,
  ThreadList,
} from "assistant-ui/react";
import { z } from "zod";

// 自定义工具（如果需要）
const getWeatherTool = makeAssistantTool({
  name: "get_weather",
  description: "获取天气信息",
  parameters: z.object({
    location: z.string().describe("城市名称"),
  }),
  execute: async ({ location }) => {
    return `今天是晴天，温度22°C。`;
  },
});

export default function DebugPage() {
  // 创建一个本地运行时，连接到我们的 API
  const runtime = useLocalRuntime({
    // 这里配置我们自己的流式端点
    stream: async (messages) => {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages }),
      });

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      return {
        async *[Symbol.asyncIterator]() {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value);
            const lines = chunk.split("\n");
            for (const line of lines) {
              if (line.startsWith("data: ")) {
                const data = line.slice(6);
                if (data === "[DONE]") return;
                try {
                  const parsed = JSON.parse(data);
                  yield parsed;
                } catch (e) {
                  // ignore
                }
              }
            }
          }
        },
      };
    },
  }, { tools: [getWeatherTool] });

  return (
    <div className="h-full flex flex-col">
      <h1 className="text-2xl font-bold mb-4">对话调试</h1>
      <div className="flex-1 min-h-0 border rounded-lg overflow-hidden">
        <AssistantRuntimeProvider runtime={runtime}>
          <div className="flex h-full">
            <div className="w-64 border-r">
              <ThreadList />
            </div>
            <div className="flex-1 flex flex-col">
              <Thread />
            </div>
          </div>
        </AssistantRuntimeProvider>
      </div>
    </div>
  );
}