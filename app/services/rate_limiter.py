import asyncio
import time
from typing import Dict
from app.config import settings

class RedisRateLimiter:
    """
    محدودکننده نرخ ارسال بر اساس chat_id.
    از Redis استفاده می‌کند تا در چند Worker هماهنگ باشد.
    """
    def __init__(self, redis_client):
        self.redis = redis_client
        self.max_per_sec = settings.RATE_LIMIT_PER_SECOND
        self.min_delay = settings.MIN_DELAY_PER_CHAT

    async def acquire(self, chat_id: int) -> None:
        key = f"rl:chat:{chat_id}:{int(time.time())}"
        # atomic increment
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, 2)

        if count > self.max_per_sec:
            await asyncio.sleep(1.0)

        # per-chat minimal delay
        last_key = f"rl:last:{chat_id}"
        now = time.time()
        last = await self.redis.get(last_key)
        if last:
            elapsed = now - float(last)
            if elapsed < self.min_delay:
                await asyncio.sleep(self.min_delay - elapsed)
        await self.redis.set(last_key, time.time(), ex=10)
