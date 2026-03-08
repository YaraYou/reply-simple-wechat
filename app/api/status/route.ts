// app/api/status/route.ts
import { NextResponse } from "next/server";

export async function GET() {
  // 模拟从 Python 后端获取的状态
  return NextResponse.json({
    status: "running", // 可选: running, stopped, error
    uptime: "2天3小时",
    todayMessages: 128,
    pendingTasks: 3,
    lastActive: "2026-03-08 14:23:45",
  });
}