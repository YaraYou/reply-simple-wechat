from __future__ import annotations

from loguru import logger
import time
import sys
import random
import datetime as dt
import warnings

warnings.filterwarnings(
    "ignore",
    message=".*pin_memory.*no accelerator is found.*",
    category=UserWarning,
)

from app.config import settings
from bot.analyzer import MessageAnalyzer
from bot.chat_ocr_parser import ChatOCRParser
from bot.conversation_manager import ConversationManager
from bot.memory_extractor import MemoryExtractor
from bot.reminders import ReminderStore
from bot.wechat_client import WeChatClient
from bot import reply
from memory import short_memory
from utils import clean_text_safe

logger.remove()
logger.add(sys.stdout, level="INFO", format="{time} | {level} | {message}")
logger.add("bot.log", rotation="10 MB", retention="7 days", level="DEBUG")


def add_to_vector_db(user_msg, assistant_msg):
    """Persist current dialogue turn into vector DB for retrieval-augmented style examples."""
    current_collection = reply.get_collection()
    if current_collection is None:
        logger.debug("Vector DB unavailable, skip incremental save")
        return

    try:
        user_clean = clean_text_safe(user_msg)
        assistant_clean = clean_text_safe(assistant_msg)
        if not user_clean or not assistant_clean:
            logger.debug("Empty message after clean, skip")
            return

        dialogue_doc = f"对方：{user_clean}\n我：{assistant_clean}"
        doc_id = f"inc_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
        current_collection.add(
            documents=[dialogue_doc],
            metadatas=[{"user": user_clean, "assistant": assistant_clean}],
            ids=[doc_id],
        )
        logger.debug(f"Added message pair to vector db: {user_clean[:20]}...")
    except Exception as e:
        logger.error(f"Failed to add message pair to vector db: {e}")


def _process_due_reminders(
    client: WeChatClient,
    reminder_store: ReminderStore,
    now_dt: dt.datetime,
    bot_start_time: dt.datetime,
):
    due_tasks = reminder_store.pop_due_tasks(now=now_dt, allow_overdue=False, overdue_before=bot_start_time)
    for task in due_tasks:
        reminder_text = f"提醒：{task.summary}"
        client.send_message(reminder_text, source="internal_reminder")
        logger.info(f"Triggered reminder task={task.id} sender={task.sender} due_at={task.due_at}")


def _handle_task_intent(analysis, sender: str, raw_message: str, reminder_store: ReminderStore, now_dt: dt.datetime):
    task = reminder_store.add_task_from_analysis(
        sender=sender,
        raw_message=raw_message,
        analysis=analysis.to_dict(),
        now=now_dt,
    )
    if task is not None:
        logger.info(f"Task stored id={task.id} due_at={task.due_at}")


def main():
    logger.info("Starting WeChat bot...")
    logger.info("Make sure WeChat window is open and focused on the target chat")
    input("Press Enter to start...")

    client = WeChatClient()
    analyzer = MessageAnalyzer(mode=settings.analyzer_mode, rule_fallback=True)
    reminder_store = ReminderStore(file_path=settings.reminders_file)
    chat_parser = ChatOCRParser()
    conversation_manager = ConversationManager(max_messages=80, min_confidence=0.35, confirm_rounds=2)
    conversation_manager.set_recently_sent_matcher(client.match_recently_sent)
    memory_extractor = MemoryExtractor()
    bot_start_time = dt.datetime.now()

    logger.info(f"Listening for new messages... analyzer_mode={settings.analyzer_mode}")

    while True:
        try:
            time.sleep(0.5)
            now_dt = dt.datetime.now()
            _process_due_reminders(client, reminder_store, now_dt, bot_start_time)

            structured_context = []
            extracted_memory_items = []
            candidate_msg = None

            # 主路径：优先使用整屏 OCR 的结构化解析结果。
            # 这样可以拿到 sender/source/timestamp/confidence 等元信息，减少误触发回复。
            panel_image = client.capture_chat_panel()
            if panel_image is not None:
                parsed_messages = chat_parser.parse_image(panel_image)
                if parsed_messages:
                    new_other_messages = conversation_manager.get_new_other_messages(parsed_messages)
                    structured_context = conversation_manager.get_recent_messages(limit=12)
                    if new_other_messages:
                        candidate_msg = new_other_messages[-1]
                        extracted_memory_items = memory_extractor.extract_from_messages(new_other_messages, owner="other")

            message_meta = None
            if candidate_msg is not None:
                new_msg = candidate_msg.text
                message_meta = {
                    "sender_role": candidate_msg.sender_role,
                    "is_timestamp": candidate_msg.is_timestamp,
                    "is_noise": candidate_msg.is_noise,
                    "source": candidate_msg.source,
                    "confidence": candidate_msg.confidence,
                    "msg_id": candidate_msg.msg_id,
                }
            else:
                # 兜底路径：当整屏 OCR 没有稳定新消息时，退回到旧的"最新气泡"OCR 读取。
                # 保留该分支是为了在 OCR 解析不稳定或性能受限时仍可工作。
                new_msg = client.get_new_messages()
                if new_msg:
                    recent_source = client.match_recently_sent(new_msg)
                    message_meta = {
                        "sender_role": "other",
                        "is_timestamp": False,
                        "is_noise": False,
                        "source": recent_source,
                        "confidence": 1.0,
                        "msg_id": None,
                    }

            if not new_msg:
                continue

            sender = client.get_chat_key()
            analysis = analyzer.analyze(
                new_msg,
                sender_role=(message_meta or {}).get("sender_role"),
                is_timestamp=bool((message_meta or {}).get("is_timestamp")),
                is_noise=bool((message_meta or {}).get("is_noise")),
                source=(message_meta or {}).get("source"),
            )

            # 双重防线：即便上游已过滤，主循环仍按意图做一次最终拦截，
            # 防止后续模块变更导致噪声消息漏进回复链路。
            if analysis.intent in {"noise", "system", "self_echo"}:
                logger.debug(f"Skip message by guard: {new_msg[:40]} intent={analysis.intent}")
                continue

            logger.info(f"Received message: {new_msg[:50]}... intent={analysis.intent} conf={analysis.confidence:.2f}")

            if analysis.intent == "task":
                _handle_task_intent(analysis, sender, new_msg, reminder_store, now_dt)

            reply_text = reply.daily_reply(new_msg)
            if not reply_text:
                short_mem_str = short_memory.format_for_prompt(sender)
                reply_text = reply.get_smart_reply(
                    sender,
                    new_msg,
                    short_mem_str,
                    analysis_context=analyzer.to_reply_context(analysis),
                    structured_context=structured_context,
                    memory_items=extracted_memory_items,
                    message_meta=message_meta,
                    recently_sent_match=client.is_recently_sent(new_msg),
                )

            if not reply_text:
                continue

            if len(reply_text) > settings.reply_max_length:
                reply_text = reply_text[:settings.reply_max_length] + "..."

            client.send_message(reply_text, source="assistant")
            short_memory.add_round(
                sender,
                new_msg,
                reply_text,
                **analyzer.to_memory_kwargs(analysis),
            )

            add_to_vector_db(new_msg, reply_text)

        except KeyboardInterrupt:
            logger.info("Interrupted by user, exiting")
            break
        except Exception as e:
            logger.exception(f"Main loop error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()

