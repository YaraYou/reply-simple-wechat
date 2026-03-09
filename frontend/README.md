# frontend

ReplySimpleWeChat 控制台前端（Vite + React + TypeScript）。

## 环境变量

- `VITE_USE_MOCK=true|false`
- `VITE_API_BASE_URL=http://127.0.0.1:8000`

默认使用 mock（第一阶段）。

## 启动

```bash
npm install
npm run dev
```

## 页面与路由

- `/` Dashboard
- `/chat-monitor` Chat Monitor
- `/detection-debug` Detection Debug
- `/memory-center` Memory Center
- `/settings` Settings
- `/logs` Logs

## 说明

- 第一阶段不包含登录/鉴权。
- start/stop 通过 `/api/control/start`、`/api/control/stop` 调用控制层。
- 若后端控制层未提供，默认 mock 响应。
