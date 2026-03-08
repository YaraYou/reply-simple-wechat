// app/api/tasks/route.ts
import { NextResponse } from "next/server";

// 模拟任务数据
let tasks = [
  { id: 1, content: "提醒张三下午开会", dueTime: "15:00", completed: false },
  { id: 2, content: "给李四发周报", dueTime: "18:00", completed: true },
  { id: 3, content: "明天早上9点提醒买咖啡", dueTime: "09:00", completed: false },
];

export async function GET() {
  return NextResponse.json(tasks);
}

export async function POST(request: Request) {
  const task = await request.json();
  task.id = Date.now();
  tasks.push(task);
  return NextResponse.json(task);
}

export async function PUT(request: Request) {
  const { id, ...updates } = await request.json();
  tasks = tasks.map(t => t.id === id ? { ...t, ...updates } : t);
  return NextResponse.json({ success: true });
}

export async function DELETE(request: Request) {
  const { searchParams } = new URL(request.url);
  const id = parseInt(searchParams.get("id") || "0");
  tasks = tasks.filter(t => t.id !== id);
  return NextResponse.json({ success: true });
}