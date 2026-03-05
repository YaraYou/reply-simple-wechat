import re
import unicodedata

def clean_text_safe(text):
    """超级清洗：只保留中文、英文、数字、空格，删除所有标点符号和特殊字符"""
    if not isinstance(text, str):
        return ""
    # 1. Unicode规范化（NFKC会分解兼容字符，比如把ﬁ分解为fi）
    text = unicodedata.normalize('NFKC', text)
    # 2. 删除控制字符和不可见字符
    text = ''.join(ch for ch in text if unicodedata.category(ch)[0] != 'C')
    # 3. 只保留：中文、英文、数字、空格
    # 中文范围：\u4e00-\u9fff，英文大小写：\u0041-\u005a\u0061-\u007a，数字：\u0030-\u0039，空格：\s
    text = re.sub(r'[^\u4e00-\u9fff\u0041-\u005a\u0061-\u007a\u0030-\u0039\s]+', '', text)
    # 4. 合并多余空格并去除首尾空格
    text = re.sub(r'\s+', ' ', text).strip()
    return text