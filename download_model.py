import os
# 设置镜像源
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

from huggingface_hub import snapshot_download

print("开始下载模型，请耐心等待（约500MB）...")
try:
    snapshot_download(
        repo_id = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        local_dir="./model_cache",          # 下载到当前目录的 model_cache 文件夹
        local_dir_use_symlinks=False,       # 不使用软链接（虽会报警告，但有效）
        resume_download=True,                # 支持断点续传
        max_workers=4                        # 多线程下载
        # 注意：已移除 timeout 和 etag_timeout 参数
    )
    print("✅ 模型下载成功！保存在 ./model_cache 文件夹")
except Exception as e:
    print(f"❌ 下载失败: {e}")
    print("请检查网络或稍后重试。")
