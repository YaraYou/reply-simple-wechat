import os
import re
import glob
import chardet
import chromadb
from chromadb.utils import embedding_functions
from utils import clean_text_safe

INVALID_MSGS = {
    '[表情]', '表情', '[', '[图片]', '图片', '[语音]', '语音',
    '[动画表情]', '[语音或视频通话]', '', '[破涕为笑]', '[笑哭]'
}

def is_valid_message(text):
    text_clean = clean_text_safe(text)
    if not text_clean:
        return False
    if '[' in text_clean or '【' in text_clean or '<' in text_clean or '红包' in text_clean:
        return False
    if text_clean in INVALID_MSGS:
        return False
    if len(text_clean) < 2:
        return False
    if all(not c.isalnum() for c in text_clean):
        return False
    return True

def parse_single_file(filepath, my_name="我"):
    with open(filepath, 'rb') as f:
        raw = f.read(5000)
        result = chardet.detect(raw)
        encoding = result['encoding'] if result['encoding'] else 'utf-8'
    print(f"检测到编码: {encoding}")

    with open(filepath, 'r', encoding=encoding, errors='ignore') as f:
        lines = [line.rstrip('\n') for line in f]

    pairs = []
    i = 0
    n = len(lines)
    prev_user_msg = None

    while i < n:
        if not lines[i].strip():
            i += 1
            continue

        match = re.match(r'^(.+?)\s+\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}$', lines[i])
        if not match:
            i += 1
            continue

        sender = match.group(1).strip()
        i += 1

        content = None
        while i < n and not lines[i].strip():
            i += 1
        if i < n:
            content = lines[i].strip()
        else:
            break
        i += 1

        if content is None:
            continue

        if not is_valid_message(content):
            continue

        cleaned_user = clean_text_safe(content)

        if sender == my_name:
            if prev_user_msg is not None:
                cleaned_assistant = clean_text_safe(content)
                pairs.append((prev_user_msg, cleaned_assistant))
                prev_user_msg = None
        else:
            prev_user_msg = cleaned_user

    print(f"  提取到 {len(pairs)} 对有效对话")
    return pairs

def build_multi_turn_examples(pairs, window=3):
    """
    将单轮对话对组合成多轮示例，每个示例包含连续的 window 轮对话。
    返回列表，每个元素为格式化的多轮对话文本。
    """
    examples = []
    for i in range(len(pairs) - window + 1):
        block = pairs[i:i+window]
        # 格式化为多行文本
        lines = []
        for user, assistant in block:
            lines.append(f"对方：{user}")
            lines.append(f"你：{assistant}")
        example_text = "\n".join(lines)
        examples.append(example_text)
    return examples

def main():
    chat_dir = r"D:\wechat_bot\chat_records"
    my_name = "我"

    all_pairs = []
    for filepath in glob.glob(os.path.join(chat_dir, "*.txt")):
        print(f"处理文件: {filepath}")
        pairs = parse_single_file(filepath, my_name)
        all_pairs.extend(pairs)
    print(f"总共提取到 {len(all_pairs)} 对有效对话")

    # 构建多轮示例（例如连续3轮）
    multi_turn_examples = build_multi_turn_examples(all_pairs, window=3)
    print(f"生成 {len(multi_turn_examples)} 条多轮示例")

    # 保存示例到文件，便于检查
    with open("multi_turn_examples.txt", "w", encoding="utf-8") as f:
        for ex in multi_turn_examples:
            f.write(ex + "\n\n")

    # 初始化向量数据库
    client = chromadb.PersistentClient(path="./chroma_data")
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="./model_cache"
    )

    try:
        client.delete_collection("chat_history")
    except:
        pass
    collection = client.create_collection(
        name="chat_history",
        embedding_function=sentence_transformer_ef
    )

    # 批量添加多轮示例
    batch_size = 100
    total = len(multi_turn_examples)
    success_count = 0
    for i in range(0, total, batch_size):
        batch = multi_turn_examples[i:i+batch_size]
        ids = [f"multi_{i+idx}" for idx, _ in enumerate(batch)]
        documents = batch  # 文档内容就是多轮对话文本
        metadatas = [{"text": ex} for ex in batch]  # 元数据可保留完整文本

        try:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            success_count += len(batch)
            print(f"进度: {success_count}/{total}")
        except Exception as e:
            print(f"批量添加失败，尝试逐条添加... 错误: {e}")
            for j, ex in enumerate(batch):
                try:
                    collection.add(
                        documents=[ex],
                        metadatas=[{"text": ex}],
                        ids=[ids[j]]
                    )
                    success_count += 1
                    print(f"进度: {success_count}/{total}")
                except Exception as e2:
                    print(f"跳过问题示例：{ex[:30]}... 错误：{e2}")
                    continue

    print(f"最终成功存入 {success_count} 条多轮示例到向量数据库")

if __name__ == "__main__":
    main()