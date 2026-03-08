import glob
import os
import re

import chardet
import chromadb
from chromadb.utils import embedding_functions

from app.config import settings
from utils import clean_text_safe

INVALID_MSGS = {
    "[表情]",
    "表情",
    "[图片]",
    "图片",
    "[语音]",
    "语音",
    "",
}


def is_valid_message(text):
    text_clean = clean_text_safe(text)
    if not text_clean:
        return False
    if text_clean in INVALID_MSGS:
        return False
    if len(text_clean) < 2:
        return False
    if all(not c.isalnum() for c in text_clean):
        return False
    return True


def parse_single_file(filepath, my_name="我"):
    with open(filepath, "rb") as f:
        raw = f.read(5000)
        result = chardet.detect(raw)
        encoding = result["encoding"] if result["encoding"] else "utf-8"

    with open(filepath, "r", encoding=encoding, errors="ignore") as f:
        lines = [line.rstrip("\n") for line in f]

    pairs = []
    i = 0
    n = len(lines)
    prev_user_msg = None

    while i < n:
        if not lines[i].strip():
            i += 1
            continue

        match = re.match(r"^(.+?)\s+\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}$", lines[i])
        if not match:
            i += 1
            continue

        sender = match.group(1).strip()
        i += 1

        while i < n and not lines[i].strip():
            i += 1
        if i >= n:
            break

        content = lines[i].strip()
        i += 1

        if not is_valid_message(content):
            continue

        cleaned = clean_text_safe(content)
        if sender == my_name:
            if prev_user_msg is not None:
                pairs.append((prev_user_msg, cleaned))
                prev_user_msg = None
        else:
            prev_user_msg = cleaned

    return pairs


def build_multi_turn_examples(pairs, window=3):
    examples = []
    for i in range(len(pairs) - window + 1):
        block = pairs[i : i + window]
        lines = []
        for user, assistant in block:
            lines.append(f"对方：{user}")
            lines.append(f"我：{assistant}")
        examples.append("\n".join(lines))
    return examples


def main():
    all_pairs = []
    for filepath in glob.glob(os.path.join(settings.chat_records_dir, "*.txt")):
        pairs = parse_single_file(filepath)
        all_pairs.extend(pairs)

    multi_turn_examples = build_multi_turn_examples(all_pairs, window=3)

    with open(settings.multi_turn_examples_path, "w", encoding="utf-8") as f:
        for ex in multi_turn_examples:
            f.write(ex + "\n\n")

    client = chromadb.PersistentClient(path=settings.chroma_path)
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=settings.embedding_model_path
    )

    try:
        client.delete_collection("chat_history")
    except Exception:
        pass

    collection = client.create_collection(name="chat_history", embedding_function=sentence_transformer_ef)

    batch_size = 100
    total = len(multi_turn_examples)
    for i in range(0, total, batch_size):
        batch = multi_turn_examples[i : i + batch_size]
        ids = [f"multi_{i+idx}" for idx, _ in enumerate(batch)]
        collection.add(documents=batch, metadatas=[{"text": ex} for ex in batch], ids=ids)

    print(f"Done. inserted={total}")


if __name__ == "__main__":
    main()
