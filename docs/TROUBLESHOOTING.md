# Troubleshooting

开发问题和数据问题统一记录在这里。

## 2026-03-08

### OCR 准确率评测与误差分析
场景是对当前 OCR 能力做一次离线基准评测，样本量约 100 条。

测试口径
使用当前代码同款 EasyOCR 配置 `ch_sim + en`。
从聊天语料抽样并生成消息气泡图后识别，输出结构化报告。

评测结果
严格准确率 48.0%
业务等价准确率 70.0%（忽略空格和大小写）
归一化字符级准确率 91.92%

误差原因
主要是字符混淆，典型为 `0/O` `1/l/I` `G/6` 以及相近字形。
其次是空格和大小写差异，这类对语义影响较小但会拉低严格准确率。
少量极短文本出现空识别。

结果文件
`ocr_eval/ocr_eval_report_v2.json`
`ocr_eval/ocr_eval_samples_v2.json`

### OCR 自激回声 / 已读乱回（正式修复）
问题名称
OCR 自激回声导致机器人回复自己。

现象
- 机器人把刚发出的消息再次识别成“对方新消息”
- 时间戳或碎片文本（如 `29 22;56`）也会触发回复
- 提醒消息进入普通链路后反复触发 task 回复

触发条件
- 聊天窗口 OCR 有抖动，缺少稳定确认与来源隔离
- 发送链路没有 self echo 缓存
- 会话层没有强制过滤 `system/noise/internal`

根因分析
1. `me/other/system` 区分不稳定
2. 时间戳与噪声碎片未过滤
3. reminder 内部消息回流
4. 缺少 `processed_msg_ids + 两次确认`
5. analyzer 对垃圾输入给出正常意图

修复方案
- OCR 结构化输出补充 `is_timestamp/is_noise/source/msg_id`
- 会话层只放行 `other` 且非噪声、非时间、非内部来源
- 新增 recently sent 缓存，发送后 18 秒内高相似文本直接忽略
- 新增两次稳定出现确认机制
- reminder 增加 `internal_reminder` 来源并隔离 overdue 启动注入
- analyzer 增加 `noise/system/self_echo` 意图并降低置信度
- reply 增加最后一道 skip 保护

如何验证修复成功
- 运行 `python -m unittest -v`
- 重点测试：
  - `tests/test_self_echo.py`
  - `tests/test_reminder_isolation.py`
  - `tests/test_chat_ocr_parser.py`
  - `tests/test_conversation_manager.py`
  - `tests/test_analyzer_noise_guard.py`

后续预防措施
- 固定保留“上游过滤 + 下游兜底”双层防线
- 每次改动 OCR/提醒逻辑必须跑以上 5 组回归测试
- 将噪声样本持续加入测试集

## 变更索引

| Date | Scope | Action | Status |
| --- | --- | --- | --- |
| 2026-03-08 | OCR评测 | 100条样本离线评测与误差归因 | Done |
| 2026-03-08 | 防乱回补丁 | 自激回声/已读乱回修复并补测试 | Done |

## 维护说明

新问题继续按日期追加。
每条记录保留问题现象 原因定位 处理方式 结果四段。
涉及数据评测时，报告文件路径和口径必须写清楚。


## 2026-03-09

### parse_chats ????????????????
??
- ?? `parse_chats` ??? `FileNotFoundError`
- ??????`...sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 not found`

????
- `.env` ? `embedding_model_path` ??????????

????
- ????????????????

????
- ? `embedding_model_path` ??????????????? `model_cache`?
- ?? `python -m data_pipeline.parse_chats` ????????????????????

????
- ?? `python -m data_pipeline.parse_chats`??? `Done. inserted=...`
- ?? `python -m data_pipeline.check_vector_db`??? `count` ???????

### ?????? pin_memory ??
??
- ????????`pin_memory argument is set as true but no accelerator is found`

??
- ?? CPU ?????????????

??
- ???????? warning ?????????????????
