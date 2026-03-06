from __future__ import annotations

import datetime
import os
import re
from typing import Any, Dict, Optional

from loguru import logger

from config import settings
from utils import clean_text_safe

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

openai_client = None
collection = None
_collection_initialized = False

FALLBACK_REPLY = "现在网络不太稳定，稍后回你"


def get_openai_client():
    global openai_client
    if openai_client is not None:
        return openai_client

    if not settings.api_key:
        logger.warning("API key is empty. Set API_KEY in environment or .env")
        return None

    try:
        from openai import OpenAI

        openai_client = OpenAI(
            base_url=settings.base_url,
            api_key=settings.api_key,
            timeout=settings.timeout,
        )
        return openai_client
    except Exception as e:
        logger.error(f"OpenAI client init failed: {e}")
        return None


def get_collection():
    global collection, _collection_initialized
    if _collection_initialized:
        return collection

    _collection_initialized = True
    try:
        import chromadb
        from chromadb.utils import embedding_functions

        sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="./model_cache"
        )
        chroma_client = chromadb.PersistentClient(path="./chroma_data")
        collection = chroma_client.get_collection(
            name="chat_history",
            embedding_function=sentence_transformer_ef,
        )
        logger.info(f"Loaded vector db collection with {collection.count()} records")
    except Exception as e:
        logger.warning(f"Vector db unavailable, continuing without retrieval: {e}")
        collection = None

    return collection


def daily_reply(msg: str) -> Optional[str]:
    msg_lower = msg.lower()
    high_priority = [
        (r"干啥呢|干啥|在干嘛", "当前与你对话的是人工智障，有事请留言"),
        (r"在吗|在不", "咋了?"),
        (r"吃饭了吗|吃了没", "吃了"),
        (r"忙吗|忙不忙", "咋了"),
    ]
    for pattern, response in high_priority:
        if re.search(pattern, msg):
            return response

    mid_priority = [
        (r"谢谢|感谢", "没事"),
        (r"拜拜|再见", "拜拜"),
        (r"晚安", "晚安"),
        (r"睡了|睡觉了", "睡吧"),
        (r"你好|您好", "咋了?"),
    ]
    for pattern, response in mid_priority:
        if re.search(pattern, msg):
            return response

    low_priority = [
        (r"\b(hello|hi|hey)\b", "hi"),
        (r"\b(thx|3q)\b", "没事"),
        (r"\b(bye|goodbye)\b", "拜拜"),
        (r"\b(good night)\b", "晚安"),
    ]
    for pattern, response in low_priority:
        if re.search(pattern, msg_lower):
            return response

    if re.search(r"^[?？]{1,3}$|^[。\.]+$", msg):
        return "?"
    return None


def _intent_quick_reply(msg: str, analysis_context: Optional[Dict[str, Any]]) -> Optional[str]:
    """Intent-specific fast path.

    - greeting/feedback/task use short deterministic replies.
    - question/general continue to smart generation.
    """
    if not analysis_context:
        return None

    intent = analysis_context.get("intent")
    entities = analysis_context.get("entities") or {}

    if intent == "greeting":
        return "在呢，怎么啦？"

    if intent == "feedback":
        return "收到～不客气"

    if intent == "task":
        times = entities.get("time") or []
        if times:
            return f"收到，我记下了（{times[0]}）。"
        return "收到，我先记下这个任务。"

    return None


def _analysis_to_text(analysis_context: Optional[Dict[str, Any]]) -> str:
    if not analysis_context:
        return ""

    intent = analysis_context.get("intent", "")
    summary = analysis_context.get("summary", "")
    sentiment = analysis_context.get("sentiment", "")
    entities = analysis_context.get("entities", {})
    confidence = analysis_context.get("confidence", 0)

    return (
        "消息分析结果：\n"
        f"- 意图: {intent}\n"
        f"- 情绪: {sentiment}\n"
        f"- 置信度: {confidence:.2f}\n"
        f"- 提炼摘要: {summary}\n"
        f"- 实体: {entities}\n"
    )


def _build_prompt(msg_clean: str, short_memory_str: str, examples: str, current_time: str, analysis_text: str):
    analysis_block = f"{analysis_text}\n" if analysis_text else ""

    if examples:
        return (
            "以下是你过去和好友聊天的多轮对话示例（重点模仿说话风格，但必须回答当前话题）：\n"
            f"{examples}\n\n"
            f"当前对话上下文（最近几句）：\n{short_memory_str}\n"
            f"{analysis_block}"
            f"对方最新消息：{msg_clean}\n"
            "请用第一人称、日常口吻简短回复。"
        )

    return (
        f"对话上下文：\n{short_memory_str}\n"
        f"{analysis_block}"
        f"当前时间：{current_time}\n"
        f"对方最新消息：{msg_clean}\n"
        "请用日常聊天语气简短回复。"
    )


def _retrieve_examples(vector_collection, short_memory_str: str, msg_clean: str) -> str:
    if vector_collection is None or not msg_clean:
        return ""

    try:
        query_text = f"{short_memory_str}\n{msg_clean}" if short_memory_str else msg_clean
        results = vector_collection.query(query_texts=[query_text], n_results=3)
        docs = (results or {}).get("documents") or []
        if docs and docs[0]:
            logger.debug(f"Retrieved {len(docs[0])} examples from vector db")
            return "\n".join(docs[0])

        metadatas = (results or {}).get("metadatas") or []
        if metadatas and metadatas[0]:
            reconstructed = []
            for meta in metadatas[0]:
                user_text = clean_text_safe((meta or {}).get("user", ""))
                assistant_text = clean_text_safe((meta or {}).get("assistant", ""))
                if user_text and assistant_text:
                    reconstructed.append(f"对方：{user_text}\n我：{assistant_text}")
            if reconstructed:
                logger.debug(f"Reconstructed {len(reconstructed)} examples from metadata")
                return "\n".join(reconstructed)
    except Exception as e:
        logger.warning(f"Vector retrieval failed (ignored): {e}")

    return ""


def get_smart_reply(
    sender,
    msg,
    short_memory_str,
    llm_client=None,
    vector_collection=None,
    now: Optional[datetime.datetime] = None,
    analysis_context: Optional[Dict[str, Any]] = None,
):
    try:
        # Intent-aware fast branch for known categories.
        quick_reply = _intent_quick_reply(msg, analysis_context)
        if quick_reply:
            return quick_reply

        msg_clean = clean_text_safe(msg)
        now_dt = now or datetime.datetime.now()
        current_time = now_dt.strftime("%Y-%m-%d %H:%M")

        active_collection = vector_collection if vector_collection is not None else get_collection()
        examples = _retrieve_examples(active_collection, short_memory_str, msg_clean)

        active_client = llm_client if llm_client is not None else get_openai_client()
        if active_client is None:
            return FALLBACK_REPLY

        analysis_text = _analysis_to_text(analysis_context)
        prompt = _build_prompt(msg_clean, short_memory_str, examples, current_time, analysis_text)
        response = active_client.chat.completions.create(
            model=settings.model_name,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"你是我（{sender}）的微信聊天机器人，请模仿我的聊天风格。"
                        f"当前时间是 {current_time}。"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
        )

        reply_text = (response.choices[0].message.content or "").strip()
        reply_text = reply_text.replace("回复：", "").replace("回答：", "").strip()
        return reply_text or FALLBACK_REPLY
    except Exception as e:
        logger.error(f"Smart reply failed: {e}")
        return FALLBACK_REPLY
