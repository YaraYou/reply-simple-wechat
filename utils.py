import re
import unicodedata


def clean_text_safe(text):
    """安全清洗文本：保留中英文、数字和空白，移除控制符及标点噪声。"""
    if not isinstance(text, str):
        return ""

    # 1) Unicode 归一化，合并兼容字符形态。
    text = unicodedata.normalize("NFKC", text)

    # 2) 去除控制字符与不可见字符。
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")

    # 3) 仅保留中文、英文字母、数字与空白字符。
    text = re.sub(r"[^\u4e00-\u9fff\u0041-\u005a\u0061-\u007a\u0030-\u0039\s]+", "", text)

    # 4) 合并多余空白并去除首尾空格。
    text = re.sub(r"\s+", " ", text).strip()
    return text