from __future__ import annotations

from loguru import logger
import time
import sys
import random
import datetime as dt

from analyzer import MessageAnalyzer
from config import settings
from reminders import ReminderStore
from wechat_client import WeChatClient
from memory import short_memory
import reply
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


def _process_due_reminders(client: WeChatClient, reminder_store: ReminderStore, now_dt: dt.datetime):
    due_tasks = reminder_store.pop_due_tasks(now=now_dt)
    for task in due_tasks:
        reminder_text = f"提醒：{task.summary}"
        client.send_message(reminder_text)
        logger.info(f"Triggered reminder task={task.id} sender={task.sender} due_at={task.due_at}")


def _handle_task_intent(analysis, sender: str, raw_message: str, reminder_store: ReminderStore, now_dt: dt.datetime):
    """Persist task reminders locally; execution happens in due-task polling."""
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
    logger.info(f"Listening for new messages... analyzer_mode={settings.analyzer_mode}")

    while True:
        try:
            time.sleep(0.5)
            now_dt = dt.datetime.now()
            _process_due_reminders(client, reminder_store, now_dt)

            new_msg = client.get_new_messages()
            if not new_msg:
                continue

            sender = client.get_chat_key()
            analysis = analyzer.analyze(new_msg)
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
                )

            if len(reply_text) > settings.reply_max_length:
                reply_text = reply_text[:settings.reply_max_length] + "..."

            client.send_message(reply_text)
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
