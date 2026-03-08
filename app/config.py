from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


def _abs_path(path_value: str) -> str:
    p = Path(path_value)
    if p.is_absolute():
        return str(p)
    return str((BASE_DIR / p).resolve())


class Settings(BaseSettings):
    """Project settings loaded from environment variables and .env."""

    api_key: str = ""
    model_name: str = "ep-20260126003248-wsrww"
    base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    timeout: int = 20
    max_tokens: int = 50
    temperature: float = 0.8
    reply_max_length: int = 40
    short_memory_size: int = 3

    analyzer_mode: str = "rule"  # rule | ml
    reminders_file: str = "tasks.json"

    # Data paths (relative to repo root by default)
    chroma_path: str = "chroma_data"
    embedding_model_path: str = "model_cache"
    chat_records_dir: str = "chat_records"
    multi_turn_examples_path: str = "multi_turn_examples.txt"

    wechat_window_width: int = 900
    wechat_window_height: int = 700
    wechat_window_x: int = 50
    wechat_window_y: int = 100

    model_config = SettingsConfigDict(
        env_file=str((BASE_DIR / ".env").resolve()),
        env_file_encoding="utf-8",
    )

    def model_post_init(self, __context) -> None:
        # Normalize paths once at startup so cwd does not affect runtime.
        self.chroma_path = _abs_path(self.chroma_path)
        self.embedding_model_path = _abs_path(self.embedding_model_path)
        self.chat_records_dir = _abs_path(self.chat_records_dir)
        self.multi_turn_examples_path = _abs_path(self.multi_turn_examples_path)
        self.reminders_file = _abs_path(self.reminders_file)


settings = Settings()
