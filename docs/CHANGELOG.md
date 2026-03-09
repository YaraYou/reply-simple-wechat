# Changelog

## [Unreleased] - 2026-03-10

### Added
- 新增 `app/control_api.py`，提供控制台所需 HTTP 接口：
  - `GET /api/status`
  - `GET /api/messages/recent`
  - `GET /api/context/current`
  - `GET /api/detections/latest`
  - `GET /api/memories`
  - `GET /api/settings`
  - `POST /api/settings`
  - `GET /api/logs`
  - `POST /api/control/start`
  - `POST /api/control/stop`
- 新增前端控制台 `frontend/`（Vite + React + TypeScript）：
  - React Router declarative 路由
  - TanStack Query 数据层
  - mock 优先开发模式
  - 全局 Loading / Empty / Error 状态组件
- 新增页面与业务组件：Dashboard、Chat Monitor、Detection Debug、Memory Center、Settings、Logs。

### Changed
- 前端支持 `VITE_USE_MOCK` 与 `VITE_API_BASE_URL` 双模式切换。
- Topbar 新增 `MOCK/REAL` 模式与 API 连通状态提示（Mock Data / Connected / Disconnected / Checking）。
- Detection Debug 新增标签筛选、置信度筛选、选中高亮。
- Logs 新增级别筛选与关键字检索。
- Chat Monitor 新增消息统计卡与上下文时间线。

### Fixed
- 修复前端运行时 JSON/BOM 导致的 Vite 启动失败：
  - 现象：`Unexpected token '﻿' ... is not valid JSON`
  - 处理：将 `frontend` 关键配置文件转为 UTF-8 无 BOM。
- 明确端口使用，避免误访问 `127.0.0.1`（80 端口）导致 `ERR_CONNECTION_REFUSED`。

### Notes
- 当前控制层通过子进程控制 `python -m app.main`，不改后端核心逻辑。
- `start/stop` 已可通过前端调用；若控制 API 未启动，前端 REAL 模式会显示断连。

## [2026-03-09]
- 完成 YOLO + OCR 主链路接入与回退策略。
- 完成相关测试补充与文档更新。