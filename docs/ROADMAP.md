# ROADMAP

```txt
Project: ReplySimpleWeChat
Updated: 2026-03-08
```

## 2026-03-08 Done
- [x] 整段聊天窗口截图接入 `capture_chat_panel()`
- [x] 新增 `ChatOCRParser`，支持消息块合并与 `me/other/system` 规则判断
- [x] 新增 `ConversationManager`，实现去重、新消息检测、最近上下文维护
- [x] 新增 `MemoryExtractor`，实现规则记忆提炼（偏好/禁忌/安排/承诺/近期话题）
- [x] `main.py` 最小接入结构化链路，并保留旧回退路径
- [x] `reply.py` 增加 `structured_context`、`memory_items` 可选参数，保持旧接口兼容
- [x] 新增防乱回机制：只处理 `other`，屏蔽 `me/system/noise`
- [x] 增加 `recently sent` 缓存，避免回复自己刚发的消息
- [x] 增加 `processed_msg_ids` 去重与两次稳定确认机制
- [x] 隔离 `internal_reminder`，启动时 overdue 不直接注入普通链路
- [x] analyzer 新增 `noise/system/self_echo` 防误判意图
- [x] 全量测试通过 `42 passed, 1 skipped`

## Next

### R1 OCR稳定性
- [ ] 聊天面板 bbox 参数化到配置
- [ ] 增加多分辨率下的自动校准
- [ ] OCR 后处理规则升级（易混字符修正、空格归一化）

### R2 结构化上下文质量
- [ ] 增加跨轮次重复语义去重（不仅基于 msg_id）
- [ ] 支持上下文窗口策略切换（最近N条/最近N分钟）
- [ ] 为结构化上下文增加质量日志指标

### R3 记忆提炼迭代
- [ ] 记忆项持久化（本地文件或轻量库）
- [ ] 增加过期清理与冲突合并策略
- [ ] 将记忆命中率纳入评估

### R4 路由与响应
- [ ] 基于结构化上下文优化 intent 路由优先级
- [ ] 将任务类消息与提醒系统打通回执闭环
- [ ] 降低端到端延迟抖动
- [ ] 继续增强说话人识别鲁棒性（复杂布局/头像遮挡场景）
- [ ] 时间戳解析增强（跨天跨周边界）

## Config Targets
- `ANALYZER_MODE=rule|ml`
- `REMINDERS_FILE=tasks.json`
- `OCR_PANEL_BBOX=left,top,right,bottom` （计划）

## Definition of Done (next sprint)
- [ ] OCR 在常见分辨率下稳定输出结构化消息
- [ ] 新消息检测误触发率可控
- [ ] 记忆提炼可稳定命中高价值信息
- [ ] `python -m unittest -v` 维持全绿
