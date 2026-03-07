from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Project settings loaded from environment variables and .env."""


    # 使用环境变量 API_KEY
    api_key: str = ""
    model_name: str = "ep-20260126003248-wsrww"
    base_url: str = "https://ark.cn-beijing.volces.com/api/v3"
    timeout: int = 20
    max_tokens: int = 50
    temperature: float = 0.8
    reply_max_length: int = 40
    short_memory_size: int = 3

    # Analyzer and reminder settings.
    analyzer_mode: str = "rule"  # rule | ml
    reminders_file: str = "tasks.json"

    wechat_window_width: int = 900
    wechat_window_height: int = 700
    wechat_window_x: int = 50
    wechat_window_y: int = 100

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# 全局配置实例。
settings = Settings()
