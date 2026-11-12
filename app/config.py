from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── عمومی ──
    APP_NAME: str = "Telegram Forwarder"
    SECRET_KEY: str = "change-me"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    APP_TITLE_FA: str = "پنل فورواردر"
    APP_TITLE_EN: str = "Forwarder Panel"
    APP_TITLE_AR: str = "لوحة الإدارة"

    # ── دیتابیس ──
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/forwarder"
    SYNC_DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@db:5432/forwarder"

    # ── Redis / Celery ──
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # ── Telegram Bot ──
    BOT_TOKEN: str = ""
    ADMIN_IDS: str = ""

    # ── Telegram Userbot (Telethon) ──
    TG_API_ID: int = 0
    TG_API_HASH: str = ""
    TG_PHONE: str = ""
    TG_SESSION_NAME: str = "userbot"
    POLL_ENABLED: bool = True
    POLL_INTERVAL: int = 15          # ثانیه — فاصله‌ی چک کردن کانال‌ها
    POLL_BATCH: int = 50             # حداکثر پیام در هر چک

    # ── LLM (llama.cpp) ──
    LLAMA_SERVER_URL: str = "http://llama:8080"
    LLM_ENABLED: bool = True
    LLM_TIMEOUT: int = 60

    # ── Rate limiting ──
    RATE_LIMIT_PER_SECOND: int = 30
    MIN_DELAY_PER_CHAT: float = 0.05
    RETRY_MAX_ATTEMPTS: int = 5
    RETRY_MAX_DELAY: int = 60
    POLL_ENABLED: bool = True
    POLL_INTERVAL: int = 15
    POLL_BATCH: int = 100
    POLL_MAX_CATCHUP: int = 500   # حداکثر پیام برای کچ‌آپ پس از downtime (0 = بی‌نهایت)

    # ── Backup ──
    BACKUP_DIR: str = "/backups"
    BACKUP_RETENTION_DAYS: int = 7

    @property
    def admin_id_list(self) -> List[int]:
        return [int(x) for x in self.ADMIN_IDS.split(",") if x.strip().isdigit()]


settings = Settings()
