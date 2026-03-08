# ROADMAP

```txt
Project: ReplySimpleWeChat
Style: geek/minimal
Updated: 2026-03-08
```

## 2026-03-08 Notes
- [x] 新增：聊天窗口整段截图方案设计
- [x] 新增：消息分类与处理的规划
- [x] 修改：`memory.py`，准备支持更灵活的短期记忆策略
- [ ] 计划：实现消息块 OCR + 我方/对方消息识别

## Next

### R1 OCR Pipeline (Block-level)
- [ ] 全窗口截图 -> 消息块切分
- [ ] 消息块 OCR（内容 + 时间）
- [ ] 角色识别（me/peer）
- [ ] 结构化输出：`[{role, text, ts, bbox}]`

### R2 Intent Router
- [ ] intent -> handler 路由表固化
- [ ] question: 检索优先 + LLM 兜底
- [ ] task: 入库 + 到点触发 + 回执
- [ ] feedback/greeting: 快速路径优化

### R3 Memory Strategy
- [ ] 类型配额调参（greeting/question/task/...）
- [ ] summary-first 上下文压缩
- [ ] 记忆质量指标（命中率/相关性）

### R4 Reliability
- [ ] OCR失败恢复
- [ ] 窗口焦点丢失恢复
- [ ] 关键路径结构化日志
- [ ] 回归测试补齐

## Config Targets
- `ANALYZER_MODE=rule|ml`
- `REMINDERS_FILE=tasks.json`
- `OCR_MODE=full_window|block`

## Definition of Done (current sprint)
- [ ] block OCR 可稳定识别消息边界
- [ ] me/peer 识别准确率可用
- [ ] question/task 路由在主流程稳定运行
- [ ] `python -m unittest -v` 全绿