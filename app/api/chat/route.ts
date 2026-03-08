// app/api/chat/route.ts
import { NextResponse } from "next/server";

// 简单的流式响应模拟
export async function POST(request: Request) {
  const { messages } = await request.json();
  const lastMessage = messages[messages.length - 1].content;

  // 构造一个模拟的流式响应
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      const words = `收到你的消息: "${lastMessage}"。我是你的智能助手，正在思考...`.split(' ');
      for (const word of words) {
        const chunk = encoder.encode(`data: ${JSON.stringify({ content: word + ' ' })}\n\n`);
        controller.enqueue(chunk);
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      controller.enqueue(encoder.encode('data: [DONE]\n\n'));
      controller.close();
    },
  });

  return new NextResponse(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  });
}