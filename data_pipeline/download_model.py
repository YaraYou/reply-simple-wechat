import os

os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from huggingface_hub import snapshot_download

from app.config import settings

print("开始下载模型，请稍候...")
try:
    snapshot_download(
        repo_id="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        local_dir=settings.embedding_model_path,
        local_dir_use_symlinks=False,
        resume_download=True,
        max_workers=4,
    )
    print(f"模型下载成功，已保存到 {settings.embedding_model_path}")
except Exception as e:
    print(f"下载失败: {e}")
