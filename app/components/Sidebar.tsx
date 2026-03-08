// components/Sidebar.tsx
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, MessageSquare, CheckSquare2, Settings, Bug } from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { name: "仪表盘", href: "/dashboard", icon: LayoutDashboard },
  { name: "消息日志", href: "/messages", icon: MessageSquare },
  { name: "任务管理", href: "/tasks", icon: CheckSquare2 },
  { name: "设置", href: "/settings", icon: Settings },
  { name: "对话调试", href: "/debug", icon: Bug },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="w-64 bg-white border-r border-gray-200 p-4">
      <div className="mb-8">
        <h1 className="text-xl font-bold text-gray-800">🤖 微信机器人</h1>
      </div>
      <nav className="space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                pathname === item.href
                  ? "bg-blue-50 text-blue-700"
                  : "text-gray-700 hover:bg-gray-100"
              )}
            >
              <Icon className="h-5 w-5" />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}