from loguru import logger
import time
import sys
import random

from config import settings
from wechat_client import WeChatClient
from memory import short_memory
import reply
from utils import clean_text_safe
from memory_policy import classify_message, get_policy

logger.remove()
logger.add(sys.stdout, level="INFO", format="{time} | {level} | {message}")
logger.add("bot.log", rotation="10 MB", retention="7 days", level="DEBUG")


def add_to_vector_db(user_msg, assistant_msg):
    """将最新一轮用户/助手消息写入向量库，供后续检索示例使用。"""
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


def main():
    """机器人主循环：收消息 -> 生成回复 -> 发送 -> 记忆与向量库落盘。"""
    logger.info("Starting WeChat bot...")
    logger.info("Make sure WeChat window is open and focused on the target chat")
    input("Press Enter to start...")

    client = WeChatClient()
    logger.info("Listening for new messages...")

    while True:
        try:
            time.sleep(0.5)

            new_msg = client.get_new_messages()
            if not new_msg:
                continue

            sender = client.get_chat_key()
            logger.info(f"Received message: {new_msg[:50]}...")
            reply_text = reply.daily_reply(new_msg)

            if not reply_text:
                short_mem_str = short_memory.format_for_prompt(sender)
                reply_text = reply.get_smart_reply(sender, new_msg, short_mem_str)

            if len(reply_text) > settings.reply_max_length:
                reply_text = reply_text[:settings.reply_max_length] + "..."

            client.send_message(reply_text)

            # 根据消息内容自动识别对话类型，并使用该类型默认优先级。
            # 兼容旧调用：即使不传 conversation_type/priority，add_round 仍可运行。
            conversation_type = classify_message(new_msg)
            priority = get_policy(conversation_type).default_priority
            short_memory.add_round(
                sender,
                new_msg,
                reply_text,
                conversation_type=conversation_type,
                priority=priority,
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