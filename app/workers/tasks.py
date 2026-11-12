import asyncio
import logging
import subprocess
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

from aiogram import Bot
from redis.asyncio import Redis
from sqlalchemy.orm import Session

from app.workers.celery_app import celery
from app.config import settings
from app.database import SyncSessionLocal
from app.models import MessageQueue, MessageStatus
from app.services.forwarder import forward_one
from app.services.rate_limiter import RedisRateLimiter

logger = logging.getLogger(__name__)


def _run_async(coro):
    """
    در Python 3.12 دیگر get_event_loop() جدید نمی‌سازد.
    asyncio.run یک loop تازه می‌سازد، اجرا می‌کند و می‌بندد.
    برای Celery worker (که هر task در fork جدا اجرا می‌شود) مناسب است.
    """
    return asyncio.run(coro)


async def _process_batch():
    bot = Bot(token=settings.BOT_TOKEN)
    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    limiter = RedisRateLimiter(redis)
    try:
        with SyncSessionLocal() as db:
            batch = (
                db.query(MessageQueue)
                .filter(MessageQueue.status == MessageStatus.PENDING.value)
                .order_by(MessageQueue.created_at.asc())
                .limit(50)
                .all()
            )
            for item in batch:
                await forward_one(bot, db, item, limiter)
    finally:
        await redis.close()
        await bot.session.close()


@celery.task(name="app.workers.tasks.process_queue")
def process_queue():
    try:
        _run_async(_process_batch())
        return {"ok": True}
    except Exception as e:
        logger.exception("process_queue failed")
        return {"ok": False, "error": str(e)}


@celery.task(name="app.workers.tasks.retry_unknown")
def retry_unknown():
    with SyncSessionLocal() as db:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
        items = (
            db.query(MessageQueue)
            .filter(
                MessageQueue.status == MessageStatus.UNKNOWN.value,
                MessageQueue.updated_at < cutoff,
                MessageQueue.retry_count < settings.RETRY_MAX_ATTEMPTS,
            )
            .all()
        )
        for item in items:
            item.status = MessageStatus.PENDING.value
        db.commit()
        return {"recovered": len(items)}


@celery.task(name="app.workers.tasks.run_backup")
def run_backup():
    """
    pg_dump به URL استاندارد postgresql:// نیاز دارد، نه SQLAlchemy
    (postgresql+psycopg2://). همچنین باید پسورد را از env بگیرد.
    """
    import os
    import gzip

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = settings.BACKUP_DIR
    os.makedirs(out_dir, exist_ok=True)
    outfile = os.path.join(out_dir, f"backup_{ts}.sql.gz")

    # تبدیل URL: postgresql+psycopg2://user:pass@host:port/db → postgresql://user:pass@host:port/db
    sync_url = settings.SYNC_DATABASE_URL
    parsed = urlparse(sync_url)
    pg_url = f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port or 5432}/{parsed.path.lstrip('/')}"

    env = os.environ.copy()
    env["PGPASSWORD"] = parsed.password or ""

    cmd = [
        "pg_dump",
        "--no-password",       # پسورد از PGPASSWORD
        "--format=plain",
        "-d", pg_url,
    ]

    try:
        with gzip.open(outfile, "wb") as gz:
            subprocess.run(cmd, stdout=gz, stderr=subprocess.PIPE, env=env, check=True)

        # چرخش فایل‌های قدیمی
        cutoff = datetime.now().timestamp() - settings.BACKUP_RETENTION_DAYS * 86400
        for f in os.listdir(out_dir):
            p = os.path.join(out_dir, f)
            if os.path.isfile(p) and os.path.getmtime(p) < cutoff:
                os.remove(p)

        logger.info("Backup created: %s", outfile)
        return {"file": outfile, "size": os.path.getsize(outfile)}
    except subprocess.CalledProcessError as e:
        err = e.stderr.decode(errors="ignore") if e.stderr else str(e)
        logger.exception("backup failed")
        return {"error": err}
    except Exception as e:
        logger.exception("backup failed")
        return {"error": str(e)}
