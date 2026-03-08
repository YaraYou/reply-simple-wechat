# Changelog

> 记录项目中“实际已完成”的改动，便于回溯与发布说明。

![Status](https://img.shields.io/badge/status-active-success)
![Format](https://img.shields.io/badge/format-keep%20a%20changelog-blue)

本文件参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 结构。

## [Unreleased] - 2026-03-08

### Added
- 新增 `analyzer.py`：
  - `MessageAnalyzer` 规则引擎分类（`greeting/question/task/feedback/general`）
  - 结构化输出：`intent/entities/sentiment/summary/priority/confidence`
  - 与记忆/回复的映射方法：`to_memory_kwargs`、`to_reply_context`
- 新增 `intent_model.py`：
  - `Sentence-Transformers + LogisticRegression` 的意图分类器实现
  - 作为 `MessageAnalyzer(mode="ml")` 的后端能力
- 新增 `reminders.py`：
  - `tasks.json` 本地提醒持久化
  - 到点轮询触发（`pop_due_tasks`）
  - 时间解析（如“明天10:30”“周五3点半”）
- 新增测试：
  - `test_analyzer.py`（分类、模式切换、回退、回复分流）
  - `test_reminders.py`（提醒持久化与触发）

### Changed
- `main.py`
  - 接入 `MessageAnalyzer` 分析流程
  - 支持 `analyzer_mode` 配置（`rule/ml`）
  - 新增任务意图处理钩子并写入提醒
  - 新增到点提醒轮询触发逻辑
- `reply.py`
  - `get_smart_reply` 新增 `analysis_context`（可选，保持兼容）
  - 新增按意图快速回复分支（问候/反馈/任务）
  - 问题/普通闲聊继续走“向量检索 + LLM”路径
- `memory.py`
  - `add_round` 新增可选参数 `analysis`
  - `format_for_prompt` 支持优先使用分析摘要增强上下文质量
- `config.py`
  - 新增配置项：`analyzer_mode`、`reminders_file`
- `README.md`
  - 更新为 GitHub 展示风格（徽章、架构图、流程图、能力说明）

### Fixed
- 统一了任务意图从“仅日志”到“可持久化 + 可触发”的闭环能力。
- 完善了分析链路的降级机制：ML 不可用时自动回退规则分类。

### Verified
- `python -m unittest -v`
  - 结果：`27 passed, 2 skipped`

---

## [History]

> 早期提交可通过 Git 历史查看：
> `git log --oneline`