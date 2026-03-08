// app/settings/page.tsx
"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export default function SettingsPage() {
  const [apiKey, setApiKey] = useState("sk-xxxxx");
  const [modelName, setModelName] = useState("gpt-3.5-turbo");
  const [baseUrl, setBaseUrl] = useState("https://ark.cn-beijing.volces.com/api/v3");
  const [analyzerMode, setAnalyzerMode] = useState("rule");
  const [autoStart, setAutoStart] = useState(true);

  const handleSave = () => {
    // 这里应该调用 API 保存到后端（比如写入 .env 或配置文件）
    alert("设置已保存（模拟）");
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">设置</h1>

      <Card>
        <CardHeader>
          <CardTitle>LLM API 配置</CardTitle>
          <CardDescription>
            配置用于生成回复的大语言模型接口
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2">
            <Label htmlFor="apiKey">API Key</Label>
            <Input
              id="apiKey"
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="modelName">模型名称</Label>
            <Input
              id="modelName"
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="baseUrl">Base URL</Label>
            <Input
              id="baseUrl"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>意图分析设置</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2">
            <Label>分析模式</Label>
            <Select value={analyzerMode} onValueChange={setAnalyzerMode}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="选择模式" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="rule">规则模式 (rule)</SelectItem>
                <SelectItem value="ml">机器学习模式 (ml)</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>其他设置</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-2">
            <Switch
              id="autoStart"
              checked={autoStart}
              onCheckedChange={setAutoStart}
            />
            <Label htmlFor="autoStart">开机自动启动机器人</Label>
          </div>
        </CardContent>
      </Card>

      <Button onClick={handleSave}>保存设置</Button>
    </div>
  );
}