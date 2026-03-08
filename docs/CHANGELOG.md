# Changelog

> 记录实际已完成的改动。

![Status](https://img.shields.io/badge/status-active-success)
![Format](https://img.shields.io/badge/format-keep%20a%20changelog-blue)

## [Unreleased] - 2026-03-08

### Added
- 新增 `bot/chat_models.py`
  - `ChatMessage` 增加结构化字段：`is_timestamp/is_noise/source/msg_id`
  - `MemoryItem` 保持可扩展记忆结构
- 新增防乱回测试
  - `tests/test_self_echo.py`
  - `tests/test_reminder_isolation.py`
  - `tests/test_analyzer_noise_guard.py`
- 扩展已有测试
  - `tests/test_chat_ocr_parser.py`
  - `tests/test_conversation_manager.py`

### Changed
- `bot/chat_ocr_parser.py`
  - 增加时间戳识别与噪声碎片识别
  - 输出 `sender_role/is_timestamp/is_noise/raw_timestamp/confidence/msg_id`
  - `msg_id` 改为归一化文本 + 粗粒度位置生成，降低 OCR 抖动影响
- `bot/conversation_manager.py`
  - 增加硬过滤：仅允许 `other` 且非 `timestamp/noise/internal/self_echo`
  - 增加 `processed_msg_ids` 去重
  - 增加“两次稳定出现才确认新消息”机制
- `bot/wechat_client.py`
  - 发送后写入 recently sent 缓存
  - 新增 self echo 匹配方法，避免回声消息再次进入回复链
- `app/main.py`
  - 接入新过滤链路与消息元信息
  - reminder 发送标记 `internal_reminder`
  - 启动时 overdue reminder 不再直接注入普通回复链
- `bot/analyzer.py`
  - 新增 `noise/system/self_echo` 意图
  - 垃圾输入降置信度，不再高置信度误判
  - task 规则增加前置约束，避免“提醒”关键词误触发
- `bot/reply.py`
  - 增加最后一道 skip 防线
  - 命中 `system/noise/self_echo/短碎片` 时拒绝生成回复
- `bot/memory_extractor.py`
  - 过滤 `me/system/noise/self_echo/internal_reminder`，避免自说自话入记忆
- `bot/reminders.py`
  - 增加 `source` 和 `overdue` 字段
  - 支持 `allow_overdue=False` 的安全弹出策略

### Fixed
- 修复 OCR 自激回声 / 已读乱回
  - 不再回复自己刚发送的消息
  - 不再回复时间戳/日期/OCR 碎片
  - internal reminder 不再回流普通聊天链路

### Verified
- `python -m unittest -v`
  - 结果：`42 passed, 1 skipped`

### Docs
- 更新 `docs/README.md`
- 更新 `docs/troubleshooting.md`
- 更新 `docs/ROADMAP.md`
- 更新 `docs/CHANGELOG.md`

## [History]

> 更早版本可通过 Git 历史查看：
> `git log --oneline`
