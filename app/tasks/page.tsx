// app/tasks/page.tsx
"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Trash2 } from "lucide-react";

interface Task {
  id: number;
  content: string;
  dueTime: string;
  completed: boolean;
}

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [newContent, setNewContent] = useState("");
  const [newDueTime, setNewDueTime] = useState("12:00");
  const [loading, setLoading] = useState(true);

  const fetchTasks = async () => {
    const res = await fetch("/api/tasks");
    const data = await res.json();
    setTasks(data);
    setLoading(false);
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const addTask = async () => {
    if (!newContent.trim()) return;
    const res = await fetch("/api/tasks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: newContent, dueTime: newDueTime, completed: false }),
    });
    const task = await res.json();
    setTasks([...tasks, task]);
    setNewContent("");
  };

  const toggleTask = async (id: number, completed: boolean) => {
    await fetch("/api/tasks", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id, completed: !completed }),
    });
    setTasks(tasks.map(t => t.id === id ? { ...t, completed: !completed } : t));
  };

  const deleteTask = async (id: number) => {
    await fetch(`/api/tasks?id=${id}`, { method: "DELETE" });
    setTasks(tasks.filter(t => t.id !== id));
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">任务管理</h1>

      <Card>
        <CardHeader>
          <CardTitle>新建提醒任务</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 items-end">
            <div className="flex-1">
              <label className="text-sm text-gray-500">任务内容</label>
              <Input
                placeholder="例如：提醒张三下午开会"
                value={newContent}
                onChange={(e) => setNewContent(e.target.value)}
              />
            </div>
            <div className="w-32">
              <label className="text-sm text-gray-500">提醒时间</label>
              <Input
                type="time"
                value={newDueTime}
                onChange={(e) => setNewDueTime(e.target.value)}
              />
            </div>
            <Button onClick={addTask}>添加</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>任务列表</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div>加载中...</div>
          ) : tasks.length === 0 ? (
            <div className="text-gray-500">暂无任务</div>
          ) : (
            <ul className="space-y-3">
              {tasks.map((task) => (
                <li key={task.id} className="flex items-center justify-between border-b pb-2">
                  <div className="flex items-center space-x-3">
                    <Checkbox
                      checked={task.completed}
                      onCheckedChange={() => toggleTask(task.id, task.completed)}
                    />
                    <span className={task.completed ? "line-through text-gray-400" : ""}>
                      {task.content} ({task.dueTime})
                    </span>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => deleteTask(task.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}