# Changelog

> 记录实际已完成的改动。

![Status](https://img.shields.io/badge/status-active-success)
![Format](https://img.shields.io/badge/format-keep%20a%20changelog-blue)

## [Unreleased] - 2026-03-08

### Added
- 新增 `bot/chat_models.py`
  - `ChatMessage`：结构化聊天消息（`msg_id/sender_role/text/timestamp/raw_timestamp/bbox/confidence`）
  - `MemoryItem`：提炼记忆项（`memory_id/owner/content/memory_type/importance/created_at/expires_at`）
- 新增 `bot/chat_ocr_parser.py`
  - `ChatOCRParser.parse_image(image)`：整段聊天 OCR 解析
  - 支持 OCR 文本框按 y 轴合并、消息 ID 生成、说话人规则判断（`me/other/system`）
  - 支持时间文本提取与标准化（保留 `raw_timestamp`）
- 新增 `bot/conversation_manager.py`
  - 结构化消息去重
  - 新消息检测（重点 `other`）
  - 最近上下文维护与格式化输出
- 新增 `bot/memory_extractor.py`
  - 基于规则提炼记忆：偏好、禁忌、安排、承诺、近期话题
  - 记忆去重与重要度字段
- 新增测试
  - `tests/test_chat_ocr_parser.py`
  - `tests/test_conversation_manager.py`
  - `tests/test_memory_extractor.py`

### Changed
- `bot/wechat_client.py`
  - 新增 `capture_chat_panel()`：截取整段聊天消息区域
  - 保持 `send_message` 与 `get_new_messages` 旧接口不变
- `app/main.py`
  - 最小接入整段聊天解析链路：截图 -> OCR 结构化 -> 新消息检测 -> 记忆提炼
  - 若结构化链路未拿到新消息，回退原 `get_new_messages()` 逻辑
  - 回复阶段新增传入 `structured_context` 与 `memory_items`（可选）
- `bot/reply.py`
  - `get_smart_reply(...)` 新增可选参数
    - `structured_context=None`
    - `memory_items=None`
  - 在 prompt 中可拼接结构化上下文与提炼记忆
  - 旧调用 `get_smart_reply(sender, msg, short_memory_str)` 仍兼容
- `docs/README.md`
  - 更新架构图、流程图、目录结构、接口兼容说明
  - 同步新增模块与测试状态

### Fixed
- 修复结构化时间提取误匹配顺序问题
  - 优先匹配完整日期/昨天/星期
  - 再匹配 `HH:MM`

### Verified
- `python -m unittest -v`
  - 结果：`33 passed, 1 skipped`

## [History]

> 更早版本可通过 Git 历史查看：
> `git log --oneline`
