# ReplySimpleWeChat

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)
![Tests](https://img.shields.io/badge/tests-27%20passed%20%7C%201%20skipped-brightgreen)
![Intent](https://img.shields.io/badge/intent-rule%20%2F%20ml-orange)
![Status](https://img.shields.io/badge/status-active-success)

微信个人助手（桌面自动化 + 消息分析分类 + 多轮记忆 + 向量检索 + 智能回复）

</div>

## 项目简介
面对微信无官方API的现状，选择桌面自动化+OCR的替代方案实现消息交互；针对窗口焦点被抢占、分辨率变化导致的自动化失效问题，设计了基于OpenCV模板匹配的窗口状态检测与自动恢复机制；为解决纯规则意图分类的泛化瓶颈，预留了轻量级BERT模型的插拔接口，并规划了基于历史对话的在线学习路径。
- 先对消息做意图分析（问候、问题、任务、反馈、闲聊）
- 再根据意图采用不同处理策略
- 结合短期记忆和历史向量检索生成更像“你”的回复

## 核心能力
- 微信窗口自动化：OCR 读取消息 + GUI 自动发送
- MessageAnalyzer：支持 `rule/ml` 模式，默认 `rule`，`ml` 失败自动回退规则
- 多轮记忆策略：按类型差异化保留轮次，任务类更稳（更高优先级）
- 向量检索增强：ChromaDB 检索历史对话示例，增强回复风格一致性
- 本地提醒持久化：任务写入 `tasks.json`，到点触发提醒

## 性能指标（基于100条真实对话测试）
- 自动化消息读取成功率：95%（改进前约70%）
- 意图分类准确率（规则模式）：86%
- 端到端平均响应延迟：3.2秒（其中OCR 0.4秒，LLM 2.5秒，其余为调度开销）
- OCR 业务等价准确率：70%（详细误差分析见 [troubleshooting.md](troubleshooting.md)）

## 技术选型权衡
OCR
选用 EasyOCR 因其轻量、中文支持好，且无需额外服务。相比 PaddleOCR 启动更快，但准确率稍低，通过自定义词典和归一化后处理可缓解，详见 [troubleshooting.md](troubleshooting.md)。

向量库
ChromaDB 嵌入项目方便，无需独立部署，适合个人项目。未来数据量增大时可迁移至 FAISS 或 Qdrant。

意图分类
当前规则模式快速可用，但泛化能力有限。已在 `intent_model.py` 中预留 BERT 接口，计划用历史聊天记录微调 `bert-tiny` 替换。
## 架构图
```mermaid
graph LR
  W["WeChat Desktop"] --> C["bot/wechat_client.py"]
  C --> M["app/main.py"]

  M --> A["bot/analyzer.py\nMessageAnalyzer"]
  M --> R["bot/reply.py\nReply Router + LLM"]
  M --> S["memory/memory.py\nShortTermMemory"]
  M --> T["bot/reminders.py\nReminderStore"]

  R --> V["ChromaDB\nchroma_data/"]
  R --> L["OpenAI-compatible API"]

  D["data_pipeline/parse_chats.py"] --> V
  D2["data_pipeline/download_model.py"] --> E["model_cache/"]

  CFG["app/config.py + .env"] --> M
  CFG --> R
  CFG --> T
```

## 消息处理流程
```mermaid
flowchart TD
  A[收到新消息] --> B[MessageAnalyzer.analyze]
  B --> C{intent}

  C -->|greeting / feedback| D[快速回复]
  C -->|task| E[写入 tasks.json + 快速确认]
  C -->|question / general| F[短期记忆 + 向量检索 + LLM]

  D --> G[发送回复]
  E --> G
  F --> G

  G --> H[写入 ShortTermMemory]
  H --> I[增量写入向量库]
  I --> J[循环监听下一条消息]
```

## 当前目录结构
```text
.
├─ app/
│  ├─ config.py              # 全局配置与路径归一化（绝对路径）
│  └─ main.py                # 主流程入口
├─ bot/
│  ├─ analyzer.py            # 消息分析与分类（rule/ml）
│  ├─ intent_model.py        # ML 意图分类器封装
│  ├─ reminders.py           # 本地任务提醒持久化与到点触发
│  ├─ reply.py               # 回复路由、向量检索、LLM 调用
│  └─ wechat_client.py       # 微信窗口自动化/OCR
├─ memory/
│  ├─ memory.py              # ShortTermMemory
│  └─ memory_policy.py       # 记忆类型与保留策略
├─ data_pipeline/
│  ├─ parse_chats.py         # 聊天记录解析并写入向量库
│  └─ download_model.py      # 下载本地 embedding 模型
├─ utils/
│  ├─ text.py                # 文本清洗
│  └─ mouse_pos.py           # 鼠标定位辅助
├─ tests/                    # unittest 测试集
├─ chroma_data/              # 向量数据库
├─ model_cache/              # 本地 embedding 模型
├─ chat_records/             # 聊天记录原始文本
├─ tasks.json                # 本地提醒任务存储
├─ CHANGELOG.md
└─ ROADMAP.md
```

## 快速开始
### 1) 环境要求
- Windows
- Python 3.10+
- 微信 PC 客户端已登录并可见目标聊天窗口

### 2) 安装依赖
```bash
pip install loguru pydantic-settings openai
pip install pyautogui pygetwindow pyperclip pillow numpy easyocr
pip install chromadb sentence-transformers huggingface_hub chardet scikit-learn
```

### 3) 配置 `.env`
在项目根目录创建或修改 `.env`：
```env
API_KEY=your_api_key
MODEL_NAME=your_model_name_if_needed
BASE_URL=https://ark.cn-beijing.volces.com/api/v3
ANALYZER_MODE=rule
```

### 4) 启动
```bash
python -m app.main
```

## 数据准备（可选）
### 下载 embedding 模型到本地
```bash
python -m data_pipeline.download_model
```

### 解析聊天记录并构建向量库
```bash
python -m data_pipeline.parse_chats
```

## 配置说明
配置文件位于 [app/config.py](app/config.py)。
关键点：
- 所有数据路径会在启动时自动转换为“项目根目录绝对路径”，避免因工作目录不同导致找不到 `model_cache/chroma_data/.env`。
- `analyzer_mode` 支持 `rule` 或 `ml`。
- `reminders_file` 默认 `tasks.json`。

## 测试
运行：
```bash
python -m unittest -v
```

当前状态（2026-03-08）：
- 27 passed
- 1 skipped（手动 GUI 集成测试）

## 已知限制
- 依赖微信窗口焦点与 OCR，分辨率/缩放变化会影响识别稳定性
- GUI 自动化在远程桌面或抢焦点场景下可能不稳定
- 任务提醒目前是本地文件持久化 + 轮询触发

## Roadmap
详见 [ROADMAP.md](ROADMAP.md)。

## Changelog
详见 [CHANGELOG.md](CHANGELOG.md)。



