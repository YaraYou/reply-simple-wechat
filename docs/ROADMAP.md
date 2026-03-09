# ROADMAP

Project: ReplySimpleWeChat  
Updated: 2026-03-10

## 已完成（Done）

### 2026-03-08 ~ 2026-03-09
- 结构化聊天解析链路稳定化（OCR + ConversationManager + MemoryExtractor）。
- 防乱回机制完善（noise/system/self_echo 过滤、recently sent、两次确认）。
- YOLO + OCR 主链路接入，整屏 OCR 作为 fallback。

### 2026-03-10
- 控制层 API 落地：`app/control_api.py`。
- 前端控制台落地：`frontend/`。
- 六大页面与核心组件骨架完成并进入可用阶段。
- mock/real 双模式切换落地（`VITE_USE_MOCK` + `VITE_API_BASE_URL`）。
- 联真提示落地（Topbar 实时显示连接状态）。

## 进行中（In Progress）
- 控制 API 与机器人运行态数据进一步对齐（减少基于日志推断的字段）。
- Settings 写回后与运行中实例热更新策略完善（当前重启后生效最稳定）。

## 下一阶段（Next）

### R1 控制层增强
- [ ] 为 `start/stop` 增加更细状态：`starting/stopping/failed`。
- [ ] 增加健康检查接口：`GET /api/health`。
- [ ] 日志查询支持分页与时间范围过滤。

### R2 前端交互增强
- [ ] Logs 页面增加自动滚动与暂停跟随。
- [ ] Detection Debug 增加 bbox 叠加可视化（图上绘框）。
- [ ] Settings 页保存结果增加字段级反馈。

### R3 数据真实性增强
- [ ] `messages/context/detections/memories` 对接更直接的数据源，减少 mock/fallback 字段。
- [ ] 为每个接口补充 schema 校验与空值兜底。

### R4 交付与运维
- [ ] 增加一键启动脚本（同时拉起 control_api + frontend）。
- [ ] 增加部署与回滚说明文档。
- [ ] 补充前后端联调检查清单。