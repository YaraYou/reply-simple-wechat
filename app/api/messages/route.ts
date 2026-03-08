// app/api/messages/route.ts
import { NextResponse } from "next/server";

export async function GET() {
  // 模拟最近10条消息
  return NextResponse.json({
    messages: [
      { id: 1, sender: "张三", content: "你好，在吗？", intent: "greeting", reply: "在的，有什么可以帮您？", time: "14:20" },
      { id: 2, sender: "李四", content: "帮我订一张明天去北京的机票", intent: "task", reply: "好的，已记录任务", time: "14:15" },
      { id: 3, sender: "王五", content: "这个功能怎么用？", intent: "question", reply: "请查看使用文档", time: "14:10" },
      // 更多数据...
    ],
  });
}